from __future__ import annotations
import io
import os
from datetime import datetime
from typing import List, Tuple

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import pandas as pd

ALLOWED_EXTS = {".xlsx", ".xls", ".csv"}
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB

app = Flask(__name__)
CORS(app)  # allow dev server (Vite) to call the API
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Memory cache for downloadable reports (replace with Redis/S3 in prod)
REPORT_CACHE: dict[str, bytes] = {}

# HTML template for the frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel Summarizer - Smart Data Analysis</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root{
            --radius: 16px;
            --radius-lg: 24px;
            --glass-bg: rgba(15, 23, 42, 0.6);
            --glass-border: rgba(148, 163, 184, 0.18);
            --shadow-soft: 0 10px 30px -10px rgba(0,0,0,.35);
            --shadow-strong: 0 20px 60px -20px rgba(0,0,0,.45);
            --accent-start: #60a5fa; /* blue-400 */
            --accent-end: #a78bfa;   /* violet-400 */
        }

        html, body { font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; }

        .drag-over { border-color: #3b82f6; background-color: #1e40af20; transform: scale(1.02); }
        .loading { opacity: 0.6; pointer-events: none; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .hero-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); }
        .animate-float { animation: float 3s ease-in-out infinite; }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }

        /* Permanent ambient animations */
        .animated-bg { position: fixed; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; }
        .bg-blob { position: absolute; border-radius: 9999px; filter: blur(80px); opacity: .25; mix-blend-mode: screen; }
        .blob-1 { width: 36rem; height: 36rem; left: -10rem; top: -8rem; background: radial-gradient(circle at 30% 30%, #60a5fa, transparent 60%); animation: floatSlow 22s ease-in-out infinite; }
        .blob-2 { width: 28rem; height: 28rem; right: -8rem; top: 10rem; background: radial-gradient(circle at 70% 30%, #a78bfa, transparent 60%); animation: floatSlow 26s ease-in-out infinite reverse; }
        .blob-3 { width: 32rem; height: 32rem; left: 20%; bottom: -10rem; background: radial-gradient(circle at 50% 50%, #34d399, transparent 60%); animation: floatSlow 24s ease-in-out infinite; }
        @keyframes floatSlow { 0%, 100% { transform: translateY(0) translateX(0) scale(1); } 50% { transform: translateY(-16px) translateX(10px) scale(1.03); } }

        /* Reveal on scroll */
        .reveal { opacity: 0; transform: translateY(12px); transition: opacity .6s ease, transform .6s ease; }
        .reveal.visible { opacity: 1; transform: none; }

        /* Pulsing call-to-action */
        .btn-pulse { box-shadow: 0 0 0 0 rgba(59,130,246,0.6); animation: pulseGlow 2.2s infinite; }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(59,130,246,0.5); } 70% { box-shadow: 0 0 0 18px rgba(59,130,246,0); } 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); } }

        /* Subtle glow card */
        .glow-card { box-shadow: inset 0 0 0 1px rgba(148,163,184,0.15), 0 10px 30px -10px rgba(59,130,246,0.25); }

        /* Glassmorphism utility */
        .glass{ background: var(--glass-bg); backdrop-filter: saturate(140%) blur(10px); -webkit-backdrop-filter: saturate(140%) blur(10px); border: 1px solid var(--glass-border); border-radius: var(--radius-lg); }

        /* Buttons */
        .btn{ display:inline-flex; align-items:center; justify-content:center; border-radius: 9999px; padding: .875rem 1.25rem; font-weight: 600; transition: all .25s ease; }
        .btn:focus-visible{ outline: none; box-shadow: 0 0 0 3px rgba(99,102,241,.35); }
        .btn-primary{ color: #0b1020; background: linear-gradient(135deg, var(--accent-start), var(--accent-end)); }
        .btn-primary:hover{ filter: brightness(1.08); transform: translateY(-1px); }
        .btn-outline{ color: #fff; border: 2px solid rgba(255,255,255,.9); }
        .btn-outline:hover{ background: rgba(255,255,255,.9); color: #4c1d95; transform: translateY(-1px); }
    </style>
</head>
<body class="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white min-h-screen">
    <!-- Animated background blobs -->
    <div class="animated-bg">
        <div class="bg-blob blob-1"></div>
        <div class="bg-blob blob-2"></div>
        <div class="bg-blob blob-3"></div>
    </div>
    <!-- Navigation -->
    <nav class="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-chart-line text-white text-xl"></i>
                    </div>
                    <span class="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        Excel Summarizer
                    </span>
                </div>
                <div class="hidden md:flex items-center space-x-6">
                    <a href="#features" class="text-slate-300 hover:text-white transition-colors">Features</a>
                    <a href="#how-it-works" class="text-slate-300 hover:text-white transition-colors">How it Works</a>
                    <a href="#upload" class="text-slate-300 hover:text-white transition-colors">Upload</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-gradient py-20 px-6">
        <div class="max-w-7xl mx-auto text-center">
            <div class="animate-float mb-8 reveal" data-animate>
                <i class="fas fa-chart-pie text-6xl text-white/90"></i>
            </div>
            <h1 class="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent reveal" data-animate>
                Smart Excel Analysis
            </h1>
            <p class="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto reveal" data-animate>
                Transform your Excel data into actionable insights with instant client-wise and zone-wise summaries
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center items-center reveal" data-animate>
                <a href="#upload" class="btn btn-primary shadow-lg btn-pulse">
                    <i class="fas fa-upload mr-2"></i>Start Analyzing
                </a>
                <a href="#features" class="btn btn-outline">
                    <i class="fas fa-info-circle mr-2"></i>Learn More
                </a>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-20 px-6 bg-slate-800/30">
        <div class="max-w-7xl mx-auto">
            <h2 class="text-4xl font-bold text-center mb-16 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Powerful Features
            </h2>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="card-hover glow-card bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-file-excel text-2xl text-white"></i>
                    </div>
                    <h3 class="text-xl font-semibold mb-4">Multi-Format Support</h3>
                    <p class="text-slate-300">Upload Excel (.xlsx, .xls) and CSV files up to 200MB for comprehensive analysis</p>
                </div>
                <div class="card-hover glow-card bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-chart-bar text-2xl text-white"></i>
                    </div>
                    <h3 class="text-xl font-semibold mb-4">Instant Insights</h3>
                    <p class="text-slate-300">Get real-time client-wise and zone-wise summaries with completion percentages</p>
                </div>
                <div class="card-hover glow-card bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-download text-2xl text-white"></i>
                    </div>
                    <h3 class="text-xl font-semibold mb-4">Excel Reports</h3>
                    <p class="text-slate-300">Download comprehensive Excel reports with Raw Data, Client Summary, and Zone Summary sheets</p>
                </div>
            </div>
        </div>
    </section>

    <!-- How It Works Section -->
    <section id="how-it-works" class="py-20 px-6">
        <div class="max-w-7xl mx-auto">
            <h2 class="text-4xl font-bold text-center mb-16 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                How It Works
            </h2>
            <div class="grid md:grid-cols-4 gap-8">
                <div class="text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                        1
                    </div>
                    <h3 class="text-lg font-semibold mb-2">Upload File</h3>
                    <p class="text-slate-300">Drag & drop or browse your Excel/CSV file</p>
                </div>
                <div class="text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                        2
                    </div>
                    <h3 class="text-lg font-semibold mb-2">Process Data</h3>
                    <p class="text-slate-300">Our AI analyzes your data in seconds</p>
                </div>
                <div class="text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                        3
                    </div>
                    <h3 class="text-lg font-semibold mb-2">View Results</h3>
                    <p class="text-slate-300">See instant summaries and insights</p>
                </div>
                <div class="text-center reveal" data-animate>
                    <div class="w-16 h-16 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                        4
                    </div>
                    <h3 class="text-lg font-semibold mb-2">Download Report</h3>
                    <p class="text-slate-300">Get your comprehensive Excel report</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Upload Section -->
    <section id="upload" class="py-20 px-6 bg-slate-800/30">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Start Analyzing Your Data
            </h2>
            
            <!-- File Drop Zone -->
            <div id="dropZone" class="border-3 border-dashed border-slate-600 rounded-2xl p-12 text-center hover:border-slate-500 transition-all duration-300 cursor-pointer bg-slate-800/30 backdrop-blur-sm card-hover reveal" data-animate>
                <div class="text-6xl mb-6 text-blue-400">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <div class="text-2xl font-semibold mb-3">Drop your Excel/CSV file here</div>
                <div class="text-slate-400 mb-6 text-lg">or click to browse files</div>
                <input type="file" id="fileInput" accept=".xlsx,.xls,.csv" class="hidden">
                <div class="text-sm text-slate-500 bg-slate-700/50 rounded-lg px-4 py-2 inline-block">
                    <i class="fas fa-info-circle mr-2"></i>Supports .xlsx, .xls, .csv files up to 200MB
                </div>
            </div>

            <!-- Loading State -->
            <div id="loading" class="hidden mt-8 rounded-2xl bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6">
                <div class="flex items-center space-x-4 mb-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <div class="text-lg">Analyzing <span id="fileName" class="font-medium text-blue-400"></span>…</div>
                </div>
                <div class="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                    <div class="h-3 bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse rounded-full" style="width:60%"></div>
                </div>
            </div>

            <!-- Error Display -->
            <div id="error" class="hidden mt-8 rounded-2xl bg-red-950/40 border border-red-800 text-red-300 p-6">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-exclamation-triangle text-xl"></i>
                    <span id="errorMessage"></span>
                </div>
            </div>

            <!-- Results -->
            <div id="results" class="hidden mt-8 space-y-6 reveal" data-animate>
                <!-- Filters -->
                <div class="glass p-6 sticky top-16 z-30 reveal" data-animate>
                    <div class="flex flex-col md:flex-row gap-4 items-end">
                        <div class="flex-1">
                            <label for="filterZone" class="block text-sm text-slate-300 mb-1">Zone</label>
                            <select id="filterZone" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2"></select>
                        </div>
                        <div class="flex-1">
                            <label for="filterClient" class="block text-sm text-slate-300 mb-1">Client Name</label>
                            <select id="filterClient" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2"></select>
                        </div>
                        <div class="flex-1">
                            <label for="filterState" class="block text-sm text-slate-300 mb-1">State</label>
                            <select id="filterState" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2"></select>
                        </div>
                        <div class="flex-1">
                            <label for="filterCompletionMin" class="block text-sm text-slate-300 mb-1">Min Completion %</label>
                            <input id="filterCompletionMin" type="number" min="0" max="100" step="1" placeholder="0" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2" />
                        </div>
                        <div class="flex items-center gap-2 mb-1">
                            <input id="filterCancelledOnly" type="checkbox" class="h-4 w-4" />
                            <label for="filterCancelledOnly" class="text-sm text-slate-300">Cancelled only</label>
                        </div>
                        <div class="flex gap-2">
                            <button id="filtersReset" class="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg">Reset</button>
                        </div>
                    </div>
                </div>
                <div class="glass p-6 text-center">
                    <div class="flex gap-4 items-center justify-center mb-6">
                        <a id="downloadBtn" class="btn btn-primary shadow-lg btn-pulse" href="#">
                            <i class="fas fa-download mr-2"></i>Download Excel Report
                        </a>
                        <div class="text-green-200 text-sm bg-green-600/30 rounded-lg px-3 py-2 glass" style="background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.25)">
                            <i class="fas fa-check-circle mr-2"></i>Includes Raw, Client Summary, Zone Summary
                        </div>
                    </div>
                </div>
                
                <div id="clientSummary" class="mb-6"></div>
                <div id="zoneSummary" class="mb-6"></div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-slate-800/50 border-t border-slate-700 py-12 px-6">
        <div class="max-w-7xl mx-auto text-center">
            <div class="flex items-center justify-center space-x-3 mb-6">
                <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <i class="fas fa-chart-line text-white"></i>
                </div>
                <span class="text-lg font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Excel Summarizer
                </span>
            </div>
            <p class="text-slate-400 mb-6 max-w-2xl mx-auto"></p>
            <div class="flex justify-center space-x-6 text-slate-400">
                <a href="https://github.com/RANVIJAY-TOMAR" target="_blank" rel="noopener" class="hover:text-white transition-colors"><i class="fab fa-github text-xl"></i></a>
                <a href="https://www.linkedin.com/in/ranvijay-singh-58182a325?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app" target="_blank" rel="noopener" class="hover:text-white transition-colors"><i class="fab fa-linkedin text-xl"></i></a>
            </div>
        </div>
    </footer>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const results = document.getElementById('results');
        const fileName = document.getElementById('fileName');
        const downloadBtn = document.getElementById('downloadBtn');
        const clientSummary = document.getElementById('clientSummary');
        const zoneSummary = document.getElementById('zoneSummary');
        const filterZone = document.getElementById('filterZone');
        const filterClient = document.getElementById('filterClient');
        const filterState = document.getElementById('filterState');
        const filterCompletionMin = document.getElementById('filterCompletionMin');
        const filterCancelledOnly = document.getElementById('filterCancelledOnly');
        const filtersReset = document.getElementById('filtersReset');
        const errorMessage = document.getElementById('errorMessage');

        // Initialize reveal-on-scroll animations (handles reduced motion)
        initRevealAnimations();

        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // GSAP base animations
        if (window.gsap) {
            gsap.registerPlugin(ScrollTrigger);
            const fadeUp = (sel, delay=0) => gsap.fromTo(sel, {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: .8, ease: 'power2.out', delay});

            fadeUp('.hero-gradient h1', .1);
            fadeUp('.hero-gradient p', .2);
            fadeUp('.hero-gradient .btn', .3);

            gsap.utils.toArray('#features .glow-card').forEach((card, i) => {
                gsap.fromTo(card, {y: 24, opacity: 0}, {y: 0, opacity: 1, duration: .9, ease: 'power3.out', scrollTrigger: {trigger: card, start: 'top 85%'}, delay: i * 0.05});
            });

            gsap.utils.toArray('#how-it-works .text-center').forEach((step, i) => {
                gsap.fromTo(step, {scale: .96, opacity: 0}, {scale: 1, opacity: 1, duration: .8, ease: 'power2.out', scrollTrigger: {trigger: step, start: 'top 85%'}, delay: i * 0.05});
            });

            gsap.fromTo('#dropZone', {scale: .98, opacity: 0}, {scale: 1, opacity: 1, duration: .8, ease: 'power2.out', scrollTrigger: {trigger: '#dropZone', start: 'top 85%'}});
        }

        // File drop handling
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) handleFile(files[0]);
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });

        async function handleFile(file) {
            // Reset UI
            error.classList.add('hidden');
            results.classList.add('hidden');
            loading.classList.remove('hidden');
            fileName.textContent = file.name;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(errorText);
                }

                const data = await response.json();
                showResults(data);
            } catch (e) {
                showError(e.message || 'Upload failed');
            } finally {
                loading.classList.add('hidden');
            }
        }

        function showResults(data) {
            downloadBtn.href = `/api/report/${data.report_key}`;
            
            window.__originalClientRows = data.client_summary || [];
            window.__originalZoneRows = data.zone_summary || [];

            initFilters(window.__originalClientRows);
            applyFilters();
            
            results.classList.remove('hidden');
            
            // Smooth scroll to results
            results.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function initFilters(rows){
            const zones = new Set();
            const clients = new Set();
            const states = new Set();
            rows.forEach(r => {
                if (r['Zone']) zones.add(r['Zone']);
                if (r['Client Name']) clients.add(r['Client Name']);
                if (r['State']) states.add(r['State']);
            });

            const buildOptions = (select, values, label) => {
                const items = ['<option value="">All ' + label + '</option>']
                    .concat(Array.from(values).sort().map(v => `<option value="${String(v)}">${String(v)}</option>`));
                select.innerHTML = items.join('');
            };

            buildOptions(filterZone, zones, 'Zones');
            buildOptions(filterClient, clients, 'Clients');
            buildOptions(filterState, states, 'States');

            [filterZone, filterClient, filterState, filterCompletionMin, filterCancelledOnly].forEach(el => {
                el && el.addEventListener('input', applyFilters);
                el && el.addEventListener('change', applyFilters);
            });
            filtersReset.addEventListener('click', () => {
                filterZone.value = '';
                filterClient.value = '';
                filterState.value = '';
                filterCompletionMin.value = '';
                filterCancelledOnly.checked = false;
                applyFilters();
            });
        }

        function applyFilters(){
            const minComp = Number(filterCompletionMin.value || 0);
            const wantCancelled = !!filterCancelledOnly.checked;
            const z = filterZone.value;
            const c = filterClient.value;
            const s = filterState.value;

            const filtered = (window.__originalClientRows || []).filter(r => {
                if (z && String(r['Zone']) !== z) return false;
                if (c && String(r['Client Name']) !== c) return false;
                if (s && String(r['State']) !== s) return false;
                const comp = Number(r['Completion%'] ?? 0);
                if (!Number.isNaN(minComp) && comp < minComp) return false;
                if (wantCancelled && Number(r['Cancelled'] ?? 0) <= 0) return false;
                return true;
            });

            // Render client table
            clientSummary.innerHTML = createTable('Zone × Client Summary', filtered);

            // Recompute zone rollup from filtered rows
            const zoneMap = new Map();
            filtered.forEach(r => {
                const key = r['Zone'] ?? '';
                if (!zoneMap.has(key)) {
                    zoneMap.set(key, { Zone: key, Cancelled: 0, Completed: 0, HOLD: 0, Pending: 0 });
                }
                const zrow = zoneMap.get(key);
                zrow.Cancelled += Number(r['Cancelled'] ?? 0);
                zrow.Completed += Number(r['Completed'] ?? 0);
                zrow.HOLD += Number(r['HOLD'] ?? 0);
                zrow.Pending += Number(r['Pending'] ?? 0);
            });
            const zoneRows = Array.from(zoneMap.values()).map(zr => {
                const grand = (zr.Cancelled + zr.Completed + zr.HOLD + zr.Pending) || 0;
                const comp = grand ? (zr.Completed / grand) * 100 : 0;
                return { ...zr, 'Grand Total': grand, 'Completion%': Number(comp.toFixed(2)) };
            });
            // Add Grand Total row similar to backend
            if (zoneRows.length) {
                const sum = zoneRows.reduce((acc, r) => ({
                    Cancelled: acc.Cancelled + r.Cancelled,
                    Completed: acc.Completed + r.Completed,
                    HOLD: acc.HOLD + r.HOLD,
                    Pending: acc.Pending + r.Pending,
                    grand: acc.grand + r['Grand Total']
                }), { Cancelled: 0, Completed: 0, HOLD: 0, Pending: 0, grand: 0 });
                const comp = sum.grand ? (sum.Completed / sum.grand) * 100 : 0;
                zoneRows.push({ Zone: 'Grand Total', Cancelled: sum.Cancelled, Completed: sum.Completed, HOLD: sum.HOLD, Pending: sum.Pending, 'Grand Total': sum.grand, 'Completion%': Number(comp.toFixed(2)) });
            }
            zoneSummary.innerHTML = createTable('Zone Rollup', zoneRows);
        }

        function showError(message) {
            errorMessage.textContent = message;
            error.classList.remove('hidden');
        }

        function createTable(title, rows) {
            if (!rows || rows.length === 0) return '';

            const allKeys = Object.keys(rows[0]);
            const preferredOrder = ['Zone', 'Client Name', 'State', 'Tier', 'Cancelled', 'Completed', 'HOLD', 'Pending', 'Grand Total', 'Completion%'];
            const orderedKeys = preferredOrder.filter(k => allKeys.includes(k)).concat(allKeys.filter(k => !preferredOrder.includes(k)));

            const headerRow = orderedKeys.map(h => `<th class="px-6 py-4 text-left bg-slate-700/50 font-semibold">${h}</th>`).join('');
            const dataRows = rows.map(row => 
                `<tr class="border-b border-slate-700 hover:bg-slate-700/30 transition-colors">${orderedKeys.map(h => 
                    `<td class="px-6 py-4">${row[h]}</td>`
                ).join('')}</tr>`
            ).join('');

            return `
                <div class="rounded-2xl bg-slate-800/50 backdrop-blur-sm border border-slate-700 overflow-hidden glow-card">
                    <div class="px-6 py-4 bg-slate-700/50 font-semibold text-lg border-b border-slate-700">
                        <i class="fas fa-table mr-3 text-blue-400"></i>${title}
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead><tr>${headerRow}</tr></thead>
                            <tbody>${dataRows}</tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        function initRevealAnimations(){
            const items = Array.from(document.querySelectorAll('[data-animate]'));
            if (!items.length) return;

            const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (prefersReduced) {
                items.forEach(el => el.classList.add('visible'));
                return;
            }

            if ('IntersectionObserver' in window) {
                const io = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add('visible');
                            io.unobserve(entry.target);
                        }
                    });
                }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
                items.forEach(el => io.observe(el));
            } else {
                const onScroll = () => {
                    items.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.top < window.innerHeight * 0.9) {
                            el.classList.add('visible');
                        }
                    });
                };
                window.addEventListener('scroll', onScroll, { passive: true });
                onScroll();
            }
        }
    </script>
</body>
</html>
"""


def _ext_ok(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTS


def _read_upload(file_storage) -> pd.DataFrame:
    name = file_storage.filename or "uploaded"
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == ".csv":
        chunks: List[pd.DataFrame] = []
        for chunk in pd.read_csv(file_storage, chunksize=100_000, low_memory=False):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    else:
        df = pd.read_excel(file_storage, sheet_name=0)  # first sheet

    df.columns = [str(c).strip() for c in df.columns]
    return df


def _require_columns(df: pd.DataFrame, required: List[str]):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing) +
            " — expected at least: Zone, Client Name, Order Status"
        )


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "zone": "Zone",
        "client": "Client Name",
        "client_name": "Client Name",
        "order_status": "Order Status",
        "status": "Order Status",
        "state": "State",
        "State": "State",
        "tier": "Tier",
        "Tier": "Tier",
    })


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["Zone", "Client Name", "Order Status"]:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip()
    return out


def _summaries(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = _normalize(df)
    _require_columns(df, ["Zone", "Client Name", "Order Status"])
    df = _coerce(df)

    status_map = {
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
        "complete": "Completed",
        "completed": "Completed",
        "hold": "HOLD",
        "pending": "Pending",
    }
    s = df["Order Status"].str.lower().str.strip().map(status_map).fillna(df["Order Status"])
    df["Order Status"] = s

    # Pivot: Zone × Client × Status (counts)
    pivot = pd.pivot_table(
        df,
        index=["Zone", "Client Name"],
        columns=["Order Status"],
        values=df.columns[0],  # any column to count
        aggfunc="count",
        fill_value=0,
    )

    for col in ["Cancelled", "Completed", "HOLD", "Pending"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["Grand Total"] = pivot[["Cancelled", "Completed", "HOLD", "Pending"]].sum(axis=1)
    pivot["Completion%"] = (pivot["Completed"] / pivot["Grand Total"]).fillna(0.0)

    # Bring optional attributes (State, Tier) back alongside the grouped keys if present
    optional_attrs: list[str] = []
    for attr in ["State", "Tier"]:
        if attr in df.columns:
            optional_attrs.append(attr)

    # Build client-level meta (first non-null value) for each (Zone, Client Name)
    meta = None
    if optional_attrs:
        meta = (
            df.dropna(subset=optional_attrs, how="all")
              .groupby(["Zone", "Client Name"], as_index=False)[optional_attrs]
              .agg(lambda s: s.dropna().iloc[0] if not s.dropna().empty else None)
        )

    # Flatten pivot and optionally merge meta
    client_df = pivot.reset_index()
    if meta is not None:
        client_df = client_df.merge(meta, on=["Zone", "Client Name"], how="left")

    # Enforce preferred display order when possible
    preferred_order = [
        "Zone",
        "Client Name",
        "State",
        "Tier",
        "Cancelled",
        "Completed",
        "HOLD",
        "Pending",
        "Grand Total",
        "Completion%",
    ]
    present = [c for c in preferred_order if c in client_df.columns]
    remainder = [c for c in client_df.columns if c not in present]
    client_df = client_df[present + remainder]

    # Zone rollup
    zone = pivot.groupby(level=0).sum(numeric_only=True)
    zone["Completion%"] = (zone["Completed"] / zone["Grand Total"]).fillna(0.0)
    zone.loc["Grand Total"] = zone.sum(numeric_only=True)
    zone.loc["Grand Total", "Completion%"] = (
        zone.loc["Grand Total", "Completed"] / max(zone.loc["Grand Total", "Grand Total"], 1)
    )

    return client_df, zone.reset_index()


def _fmt_json(df: pd.DataFrame):
    out = df.copy()
    if "Completion%" in out.columns:
        out["Completion%"] = (out["Completion%"].fillna(0) * 100).round(2)
    return out.to_dict(orient="records")


@app.post("/api/upload")
def upload():
    if "file" not in request.files:
        return ("No file part", 400)
    f = request.files["file"]
    if not f.filename:
        return ("No selected file", 400)
    if not _ext_ok(f.filename):
        return ("Unsupported file type", 400)

    df = _read_upload(f)
    client_df, zone_df = _summaries(df)

    # Build an Excel report in-memory
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Raw")
        cd = client_df.copy(); zd = zone_df.copy()
        for d in (cd, zd):
            if "Completion%" in d.columns:
                d["Completion%"] = (d["Completion%"].fillna(0) * 100).round(2)
        cd.to_excel(writer, index=False, sheet_name="Client Summary")
        zd.to_excel(writer, index=False, sheet_name="Zone Summary")
    bio.seek(0)

    key = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    REPORT_CACHE[key] = bio.getvalue()

    return jsonify({
        "client_summary": _fmt_json(client_df),
        "zone_summary": _fmt_json(zone_df),
        "report_key": key,
    })


@app.get("/api/report/<key>")
def report(key: str):
    data = REPORT_CACHE.get(key)
    if not data:
        return ("Report expired", 404)
    filename = f"summary_{key}.xlsx"
    return send_file(io.BytesIO(data),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True,
                     download_name=filename)


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)