// ==================== CONFIGURACIÓN ====================
const API_BASE = '';  // Cambiar a 'http://localhost:8000' si se ejecuta separado

// ==================== ESTADO GLOBAL ====================
let currentResult = null;
let lastFormData = null;

// ==================== UTILIDADES ====================

function showLoading(text = 'Procesando...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    loadingText.textContent = text;
    overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('active');
}

function showToast(title, message, type = 'success') {
    const container = document.getElementById('toast-container');
    
    const icons = {
        success: '✅',
        warning: '⚠️',
        error: '❌'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type]}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: 'PEN'
    }).format(value);
}

function formatPercent(value) {
    return `${value.toFixed(1)}%`;
}

// ==================== API CALLS ====================

async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${API_BASE}/api${endpoint}`, options);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error en la solicitud');
    }
    
    return response.json();
}

// ==================== HEALTH CHECK ====================

async function checkHealth() {
    try {
        const health = await apiCall('/health');
        const statusBadge = document.getElementById('model-status');
        
        if (health.modelo_entrenado) {
            statusBadge.textContent = '✅ Modelo Activo';
            statusBadge.className = 'status-badge';
        } else {
            statusBadge.textContent = '⚠️ Sin Modelo';
            statusBadge.className = 'status-badge warning';
        }
    } catch (error) {
        const statusBadge = document.getElementById('model-status');
        statusBadge.textContent = '❌ Error';
        statusBadge.className = 'status-badge error';
    }
}

// ==================== TABS ====================

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            // Remover active de todos
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activar el seleccionado
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Cargar contenido específico
            if (targetTab === 'analytics') {
                loadAnalytics();
            } else if (targetTab === 'modelo') {
                loadModelInfo();
            }
        });
    });
}

// ==================== FORMULARIO DE PREDICCIÓN ====================

function initPredictionForm() {
    const form = document.getElementById('prediction-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {};
        
        formData.forEach((value, key) => {
            // Convertir a número si es necesario
            if (['Sexo', 'Dependientes', 'PlazoReal', 'SegmentoCartera', 
                 'apoyogobierno', 'EdadDesembolsoNormalizada', 'NivelInstruccion',
                 'iAntiguedadBancarizado', 'ScoreOriginacionMicro', 
                 'Score_Sobreendeudamiento'].includes(key)) {
                data[key] = parseInt(value);
            } else if (key === 'EstadoCivil') {
                data[key] = value;
            } else {
                data[key] = parseFloat(value);
            }
        });
        
        lastFormData = data;
        
        try {
            showLoading('Evaluando riesgo...');
            const response = await apiCall('/predict', 'POST', data);
            hideLoading();
            
            currentResult = response.resultado;
            displayResults(response.resultado);
            
            // Scroll a resultados
            document.getElementById('results').scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
            
            showToast('✅ Éxito', 'Evaluación completada', 'success');
            
        } catch (error) {
            hideLoading();
            showToast('❌ Error', error.message, 'error');
        }
    });
}

function displayResults(resultado) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('result-content');
    
    const riskColors = {
        'BAJO_RIESGO': { bg: 'success', icon: '✅' },
        'MEDIO_RIESGO': { bg: 'warning', icon: '⚠️' },
        'ALTO_RIESGO': { bg: 'danger', icon: '❌' }
    };
    
    const riskConfig = riskColors[resultado.clase] || riskColors['MEDIO_RIESGO'];
    
    contentDiv.innerHTML = `
        <div class="result-header ${riskConfig.bg}">
            <div class="result-icon">${riskConfig.icon}</div>
            <div class="result-main">
                <h3>${resultado.clase.replace('_', ' ')}</h3>
                <p>Confianza: ${formatPercent(resultado.confianza)}</p>
            </div>
        </div>
        
        <div class="result-metrics">
            <div class="metric-card">
                <div class="metric-value">${formatPercent(resultado.confianza)}</div>
                <div class="metric-label">Confianza del Modelo</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${resultado.confianza}%; background: var(--primary);"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">${resultado.score_difuso.toFixed(1)}</div>
                <div class="metric-label">Score Lógica Difusa</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${resultado.score_difuso}%; background: var(--warning);"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">${resultado.interpretacion_difusa}</div>
                <div class="metric-label">Interpretación Difusa</div>
            </div>
        </div>
        
        <div class="card-section">
            <h3>📊 Distribución de Probabilidades</h3>
            <div id="prob-chart"></div>
        </div>
        
        <div class="card-section mt-3">
            <h3>📋 Información del Cliente</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Monto:</label>
                    <span>${formatCurrency(resultado.datos_entrada.monto)}</span>
                </div>
                <div class="info-item">
                    <label>Ingreso:</label>
                    <span>${formatCurrency(resultado.datos_entrada.SalarioNormalizado)}</span>
                </div>
                <div class="info-item">
                    <label>Ratio Deuda/Ingreso:</label>
                    <span>${(resultado.datos_entrada.monto / resultado.datos_entrada.SalarioNormalizado).toFixed(2)}x</span>
                </div>
                <div class="info-item">
                    <label>Score Crediticio:</label>
                    <span>${resultado.datos_entrada.ScoreOriginacionMicro}</span>
                </div>
            </div>
        </div>
    `;
    
    resultsDiv.style.display = 'block';
    
    // Renderizar gráfico de probabilidades
    renderProbabilityChart(resultado.probabilidades);
}

function renderProbabilityChart(probabilidades) {
    const categories = Object.keys(probabilidades);
    const values = Object.values(probabilidades);
    
    const colors = {
        'BAJO_RIESGO': '#10b981',
        'MEDIO_RIESGO': '#f59e0b',
        'ALTO_RIESGO': '#ef4444'
    };
    
    const trace = {
        x: categories.map(c => c.replace('_', ' ')),
        y: values,
        type: 'bar',
        marker: {
            color: categories.map(c => colors[c] || '#64748b')
        },
        text: values.map(v => `${v.toFixed(1)}%`),
        textposition: 'auto'
    };
    
    const layout = {
        title: '',
        xaxis: { title: 'Categoría de Riesgo' },
        yaxis: { title: 'Probabilidad (%)' },
        margin: { t: 20, r: 20, b: 60, l: 60 },
        height: 300
    };
    
    Plotly.newPlot('prob-chart', [trace], layout, { responsive: true });
}

// ==================== COMPARACIÓN ====================

function initComparison() {
    const compareBtn = document.getElementById('compare-btn');
    
    compareBtn.addEventListener('click', async () => {
        if (!lastFormData) {
            showToast('⚠️ Atención', 'Primero realiza una evaluación', 'warning');
            return;
        }
        
        try {
            showLoading('Comparando modelos...');
            
            // Llamadas en paralelo
            const [hybrid, mlOnly, fuzzyOnly] = await Promise.all([
                apiCall('/predict', 'POST', lastFormData),
                apiCall('/predict-only-ml', 'POST', lastFormData),
                apiCall('/predict-only-fuzzy', 'POST', lastFormData)
            ]);
            
            hideLoading();
            
            displayComparison(hybrid.resultado, mlOnly.resultado, fuzzyOnly.resultado);
            
            document.getElementById('comparison-results').style.display = 'block';
            
            showToast('✅ Éxito', 'Comparación completada', 'success');
            
        } catch (error) {
            hideLoading();
            showToast('❌ Error', error.message, 'error');
        }
    });
}

function displayComparison(hybrid, mlOnly, fuzzy) {
    document.getElementById('hybrid-result').innerHTML = createComparisonCard(hybrid);
    document.getElementById('ml-only-result').innerHTML = createComparisonCard(mlOnly);
    document.getElementById('fuzzy-only-result').innerHTML = createComparisonCard(fuzzy);
    
    renderComparisonChart(hybrid, mlOnly, fuzzy);
}

function createComparisonCard(resultado) {
    const riskEmojis = {
        'BAJO_RIESGO': '✅',
        'MEDIO_RIESGO': '⚠️',
        'ALTO_RIESGO': '❌'
    };
    
    return `
        <div class="text-center mb-3">
            <div style="font-size: 3rem;">${riskEmojis[resultado.clase]}</div>
            <h4>${resultado.clase.replace('_', ' ')}</h4>
            <p class="text-secondary">Confianza: ${formatPercent(resultado.confianza)}</p>
        </div>
        <div class="metric-card">
            <div class="metric-label">Score Difuso</div>
            <div class="metric-value" style="font-size: 1.5rem;">
                ${resultado.score_difuso ? resultado.score_difuso.toFixed(1) : 'N/A'}
            </div>
        </div>
    `;
}

function renderComparisonChart(hybrid, mlOnly, fuzzy) {
    const trace = {
        x: ['Sistema Híbrido', 'Solo ML', 'Solo Difuso'],
        y: [hybrid.confianza, mlOnly.confianza, fuzzy.confianza || 100],
        type: 'bar',
        marker: {
            color: ['#3b82f6', '#10b981', '#f59e0b']
        },
        text: [
            `${hybrid.clase}<br>${hybrid.confianza.toFixed(1)}%`,
            `${mlOnly.clase}<br>${mlOnly.confianza.toFixed(1)}%`,
            `${fuzzy.clase}<br>100%`
        ],
        textposition: 'auto'
    };
    
    const layout = {
        title: 'Comparación de Confianza por Método',
        yaxis: { title: 'Confianza (%)' },
        margin: { t: 40, r: 20, b: 60, l: 60 },
        height: 400
    };
    
    Plotly.newPlot('comparison-chart', [trace], layout, { responsive: true });
}

// ==================== ANALYTICS ====================

async function loadAnalytics() {
    try {
        const response = await apiCall('/feedback/stats');
        displayAnalytics(response.metricas);
    } catch (error) {
        document.getElementById('stats-content').innerHTML = `
            <p class="loading-text">No hay datos de feedback disponibles</p>
        `;
    }
}

function displayAnalytics(metricas) {
    const statsContent = document.getElementById('stats-content');
    
    if (metricas.total === 0) {
        statsContent.innerHTML = `
            <p class="loading-text">No hay feedback registrado aún</p>
        `;
        return;
    }
    
    statsContent.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <h4>Total Evaluaciones</h4>
                <div class="value">${metricas.total}</div>
            </div>
            <div class="stat-card">
                <h4>Predicciones Correctas</h4>
                <div class="value">${metricas.correctos}</div>
            </div>
            <div class="stat-card">
                <h4>Accuracy Real</h4>
                <div class="value">${formatPercent(metricas.accuracy_real)}</div>
            </div>
            <div class="stat-card">
                <h4>Incorrectas</h4>
                <div class="value">${metricas.incorrectos}</div>
            </div>
        </div>
    `;
    
    // Renderizar gráfico de distribución
    if (metricas.distribucion_real) {
        renderDistributionChart(metricas.distribucion_real);
    }
}

function renderDistributionChart(distribucion) {
    const chartsDiv = document.getElementById('stats-charts');
    chartsDiv.innerHTML = '<div id="distribution-chart"></div>';
    
    const labels = Object.keys(distribucion);
    const values = Object.values(distribucion);
    
    const trace = {
        labels: labels.map(l => l.replace('_', ' ')),
        values: values,
        type: 'pie',
        marker: {
            colors: ['#10b981', '#f59e0b', '#ef4444']
        }
    };
    
    const layout = {
        title: 'Distribución de Resultados Reales',
        height: 400
    };
    
    Plotly.newPlot('distribution-chart', [trace], layout, { responsive: true });
}

// ==================== MODEL MANAGEMENT ====================

async function loadModelInfo() {
    try {
        const info = await apiCall('/model/info');
        displayModelInfo(info);
    } catch (error) {
        document.getElementById('model-info-content').innerHTML = `
            <p class="loading-text">Error al cargar información del modelo</p>
        `;
    }
}

function displayModelInfo(info) {
    const content = document.getElementById('model-info-content');
    
    if (!info.entrenado) {
        content.innerHTML = `
            <div class="info-item" style="background: rgba(239, 68, 68, 0.1);">
                <label>Estado:</label>
                <span>❌ No Entrenado</span>
            </div>
            <p class="text-secondary mt-2">El modelo debe ser entrenado antes de usar el sistema.</p>
        `;
        return;
    }
    
    const metricas = info.metricas || {};
    
    content.innerHTML = `
        <div class="info-grid">
            <div class="info-item">
                <label>Estado:</label>
                <span>✅ Entrenado</span>
            </div>
            <div class="info-item">
                <label>Features:</label>
                <span>${info.features || 'N/A'}</span>
            </div>
            <div class="info-item">
                <label>Accuracy:</label>
                <span>${metricas.accuracy ? formatPercent(metricas.accuracy * 100) : 'N/A'}</span>
            </div>
            <div class="info-item">
                <label>F1-Score:</label>
                <span>${metricas.f1_score ? metricas.f1_score.toFixed(4) : 'N/A'}</span>
            </div>
        </div>
    `;
}

function initModelActions() {
    document.getElementById('train-model').addEventListener('click', async () => {
        showToast('ℹ️ Información', 
            'Para entrenar el modelo, ejecute: python train_model.py', 
            'warning');
    });
    
    document.getElementById('delete-model').addEventListener('click', async () => {
        if (!confirm('¿Está seguro de eliminar el modelo? Deberá reentrenarlo.')) {
            return;
        }
        
        try {
            showLoading('Eliminando modelo...');
            await apiCall('/model/delete', 'DELETE');
            hideLoading();
            
            showToast('✅ Éxito', 'Modelo eliminado correctamente', 'success');
            
            setTimeout(() => {
                location.reload();
            }, 2000);
            
        } catch (error) {
            hideLoading();
            showToast('❌ Error', error.message, 'error');
        }
    });
}

// ==================== UTILIDADES DE FORMULARIO ====================

function initFormHelpers() {
    document.getElementById('load-example').addEventListener('click', async () => {
        try {
            const response = await apiCall('/examples');
            const ejemplo = response.ejemplos[0].datos;
            
            // Llenar formulario
            Object.keys(ejemplo).forEach(key => {
                const input = document.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = ejemplo[key];
                }
            });
            
            showToast('✅ Éxito', 'Ejemplo cargado', 'success');
            
        } catch (error) {
            showToast('❌ Error', error.message, 'error');
        }
    });
    
    document.getElementById('clear-form').addEventListener('click', () => {
        document.getElementById('prediction-form').reset();
        showToast('✅ Éxito', 'Formulario limpiado', 'success');
    });
    
    document.getElementById('new-evaluation').addEventListener('click', () => {
        document.getElementById('results').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    // BOTÓN: Descargar Reporte
    document.getElementById('download-report').addEventListener('click', () => {
        if (!currentResult) {
            showToast('⚠️ Atención', 'No hay resultado para descargar', 'warning');
            return;
        }
        
        generatePDFReport(currentResult);
    });
    
    // BOTÓN: Registrar Feedback
    document.getElementById('register-feedback').addEventListener('click', () => {
        if (!currentResult) {
            showToast('⚠️ Atención', 'No hay resultado para registrar', 'warning');
            return;
        }
        
        showFeedbackModal(currentResult);
    });
    
    // BOTÓN: Actualizar Estadísticas
    document.getElementById('refresh-stats').addEventListener('click', () => {
        loadAnalytics();
        showToast('🔄 Actualizando', 'Cargando estadísticas...', 'success');
    });
}

// ==================== DESCARGAR REPORTE ====================

function generatePDFReport(resultado) {
    const reportContent = `
═══════════════════════════════════════════════════════════════
    REPORTE DE EVALUACIÓN DE RIESGO CREDITICIO
═══════════════════════════════════════════════════════════════

Fecha: ${new Date().toLocaleString('es-PE')}

RESULTADO DE EVALUACIÓN
───────────────────────────────────────────────────────────────

Clasificación: ${resultado.clase.replace('_', ' ')}
Confianza del Modelo: ${formatPercent(resultado.confianza)}
Score Lógica Difusa: ${resultado.score_difuso.toFixed(2)}/100
Interpretación Difusa: ${resultado.interpretacion_difusa}

PROBABILIDADES POR CATEGORÍA
───────────────────────────────────────────────────────────────

${Object.entries(resultado.probabilidades)
    .map(([cat, prob]) => `${cat.replace('_', ' ').padEnd(20)}: ${formatPercent(prob)}`)
    .join('\n')}

INFORMACIÓN DEL CLIENTE
───────────────────────────────────────────────────────────────

Monto Solicitado: ${formatCurrency(resultado.datos_entrada.monto)}
Ingreso Mensual: ${formatCurrency(resultado.datos_entrada.SalarioNormalizado)}
Ratio Deuda/Ingreso: ${(resultado.datos_entrada.monto / resultado.datos_entrada.SalarioNormalizado).toFixed(2)}x
Edad: ${resultado.datos_entrada.EdadDesembolsoNormalizada} años
Estado Civil: ${resultado.datos_entrada.EstadoCivil}
Dependientes: ${resultado.datos_entrada.Dependientes}
Antigüedad Bancaria: ${resultado.datos_entrada.iAntiguedadBancarizado} meses
Score Crediticio: ${resultado.datos_entrada.ScoreOriginacionMicro}/1000
Score Sobreendeudamiento: ${resultado.datos_entrada.Score_Sobreendeudamiento}/1000

RECOMENDACIÓN
───────────────────────────────────────────────────────────────

${resultado.clase === 'BAJO_RIESGO' ? 
'✅ APROBACIÓN RECOMENDADA - Cliente presenta bajo riesgo crediticio' :
resultado.clase === 'MEDIO_RIESGO' ?
'⚠️ REQUIERE ANÁLISIS ADICIONAL - Considerar garantías o condiciones especiales' :
'❌ RECHAZO RECOMENDADO - Cliente presenta alto riesgo de mora'}

═══════════════════════════════════════════════════════════════
    Sistema Híbrido Difuso-Neuronal v1.0
═══════════════════════════════════════════════════════════════
    `;
    
    // Crear blob y descargar
    const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `reporte_riesgo_${Date.now()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    
    showToast('✅ Éxito', 'Reporte descargado', 'success');
}

// ==================== MODAL DE FEEDBACK ====================

function showFeedbackModal(resultado) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    `;
    
    modal.innerHTML = `
        <div style="background: white; padding: 2rem; border-radius: 12px; max-width: 500px; width: 90%;">
            <h2 style="margin-bottom: 1rem; color: #0f172a;">Registrar Feedback</h2>
            <p style="color: #64748b; margin-bottom: 1.5rem;">
                El sistema predijo: <strong>${resultado.clase.replace('_', ' ')}</strong><br>
                ¿Cuál fue el resultado real?
            </p>
            
            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                <button class="feedback-option btn btn-primary" data-result="BAJO_RIESGO">
                    ✅ BAJO RIESGO (pagó correctamente)
                </button>
                <button class="feedback-option btn btn-secondary" data-result="MEDIO_RIESGO">
                    ⚠️ MEDIO RIESGO (algunos retrasos)
                </button>
                <button class="feedback-option btn btn-danger" data-result="ALTO_RIESGO">
                    ❌ ALTO RIESGO (mora >30 días)
                </button>
                <button id="cancel-feedback" class="btn" style="background: #e2e8f0; color: #0f172a;">
                    Cancelar
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Event listeners
    modal.querySelectorAll('.feedback-option').forEach(btn => {
        btn.addEventListener('click', async () => {
            const resultadoReal = btn.dataset.result;
            
            try {
                showLoading('Registrando feedback...');
                
                await apiCall('/feedback', 'POST', {
                    id_evaluacion: `EVAL_${Date.now()}`,
                    prediccion: resultado.clase,
                    resultado_real: resultadoReal,
                    datos_evaluacion: resultado
                });
                
                hideLoading();
                document.body.removeChild(modal);
                
                const correcto = resultado.clase === resultadoReal;
                showToast(
                    correcto ? '✅ Correcto' : '⚠️ Incorrecto',
                    correcto ? 'El sistema predijo correctamente' : 'Predicción diferente al resultado real',
                    correcto ? 'success' : 'warning'
                );
                
            } catch (error) {
                hideLoading();
                showToast('❌ Error', error.message, 'error');
            }
        });
    });
    
    document.getElementById('cancel-feedback').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// ==================== INICIALIZACIÓN ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando Sistema de Riesgo Crediticio...');
    
    checkHealth();
    initTabs();
    initPredictionForm();
    initComparison();
    initModelActions();
    initFormHelpers();
    
    // Actualizar health cada 30 segundos
    setInterval(checkHealth, 30000);
    
    console.log('✅ Sistema inicializado correctamente');
});