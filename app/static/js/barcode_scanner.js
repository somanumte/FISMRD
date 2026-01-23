/**
 * ============================================
 * BARCODE SCANNER INTEGRATION
 * ============================================
 * 
 * Sistema de integración con lectores de código de barras USB/Bluetooth
 * para escaneo de números de serie de fabricante.
 * 
 * Características:
 * - Detección automática de entrada de escáner vs teclado
 * - Feedback visual y auditivo
 * - Validación en tiempo real
 * - Soporte para múltiples modos de escaneo
 * - Compatible con la mayoría de escáneres USB (modo keyboard wedge)
 * 
 * Dependencias:
 * - onScan.js (incluido inline para evitar dependencias externas)
 * 
 * @author Sistema de Seriales LuxeraRD
 * @version 1.0.0
 */

// ============================================
// CONFIGURACIÓN GLOBAL
// ============================================

const BarcodeScanner = {
    // Configuración por defecto
    config: {
        // Tiempo mínimo entre caracteres para detectar escaneo (ms)
        // Los escáneres típicamente envían caracteres muy rápido (<50ms)
        minTimeBetweenChars: 50,
        
        // Tiempo máximo para considerar una secuencia como escaneo (ms)
        maxTimeBetweenChars: 100,
        
        // Longitud mínima de código válido
        minCodeLength: 3,
        
        // Longitud máxima de código válido
        maxCodeLength: 100,
        
        // Código de tecla para sufijo (Enter = 13, Tab = 9)
        suffixKeyCodes: [13],
        
        // Código de tecla para prefijo (opcional)
        prefixKeyCodes: [],
        
        // Habilitar feedback auditivo
        enableSound: true,
        
        // Habilitar feedback visual
        enableVisualFeedback: true,
        
        // Prevenir que el código se escriba en inputs
        preventDefault: true,
        
        // Endpoint de API para validación
        apiEndpoint: '/api/serials/validate',
        
        // Endpoint de API para búsqueda
        searchEndpoint: '/api/serials/search',
    },
    
    // Estado actual
    state: {
        isInitialized: false,
        isScanning: false,
        lastScan: null,
        scanCount: 0,
        currentMode: 'search', // 'search', 'add', 'sell'
        targetInput: null,
        callbacks: {},
    },
    
    // Elementos de audio para feedback
    sounds: {
        success: null,
        error: null,
        scan: null,
    },
    
    // ============================================
    // INICIALIZACIÓN
    // ============================================
    
    /**
     * Inicializa el sistema de escaneo de códigos de barras
     * @param {Object} options - Opciones de configuración
     */
    init: function(options = {}) {
        if (this.state.isInitialized) {
            console.warn('BarcodeScanner ya está inicializado');
            return;
        }
        
        // Merge opciones con configuración por defecto
        this.config = { ...this.config, ...options };
        
        // Inicializar sonidos
        this._initSounds();
        
        // Configurar detector de escaneo
        this._initScanDetector();
        
        // Inicializar UI feedback
        this._initVisualFeedback();
        
        this.state.isInitialized = true;
        console.log('🔍 BarcodeScanner inicializado correctamente');
    },
    
    /**
     * Inicializa el detector de escaneo usando técnica de timing
     */
    _initScanDetector: function() {
        let buffer = '';
        let lastKeyTime = 0;
        let timeoutId = null;
        const self = this;
        
        // Listener global de teclado
        document.addEventListener('keydown', function(e) {
            const currentTime = Date.now();
            const timeDiff = currentTime - lastKeyTime;
            
            // Si pasó mucho tiempo, resetear buffer
            if (timeDiff > self.config.maxTimeBetweenChars && buffer.length > 0) {
                buffer = '';
            }
            
            lastKeyTime = currentTime;
            
            // Detectar si es sufijo (Enter/Tab)
            if (self.config.suffixKeyCodes.includes(e.keyCode)) {
                if (buffer.length >= self.config.minCodeLength) {
                    // ¡Es un escaneo!
                    e.preventDefault();
                    e.stopPropagation();
                    
                    self._handleScan(buffer);
                }
                buffer = '';
                clearTimeout(timeoutId);
                return;
            }
            
            // Ignorar teclas de control
            if (e.ctrlKey || e.altKey || e.metaKey) {
                return;
            }
            
            // Verificar si el input es lo suficientemente rápido para ser un escáner
            if (timeDiff < self.config.minTimeBetweenChars || buffer.length === 0) {
                // Obtener el carácter
                let char = '';
                
                if (e.key && e.key.length === 1) {
                    char = e.key;
                } else if (e.keyCode >= 48 && e.keyCode <= 57) {
                    // Números 0-9
                    char = String.fromCharCode(e.keyCode);
                } else if (e.keyCode >= 65 && e.keyCode <= 90) {
                    // Letras A-Z
                    char = String.fromCharCode(e.keyCode);
                    if (!e.shiftKey) {
                        char = char.toLowerCase();
                    }
                } else if (e.keyCode === 189 || e.keyCode === 109) {
                    char = '-';
                } else if (e.keyCode === 190 || e.keyCode === 110) {
                    char = '.';
                }
                
                if (char) {
                    buffer += char;
                    
                    // Prevenir input si está configurado y parece un escaneo
                    if (self.config.preventDefault && buffer.length > 3 && timeDiff < self.config.minTimeBetweenChars) {
                        e.preventDefault();
                    }
                    
                    // Timeout para limpiar buffer si no llega más input
                    clearTimeout(timeoutId);
                    timeoutId = setTimeout(() => {
                        if (buffer.length >= self.config.minCodeLength) {
                            // Podría ser un escaneo sin sufijo
                            self._handlePossibleScan(buffer);
                        }
                        buffer = '';
                    }, self.config.maxTimeBetweenChars * 2);
                }
            } else {
                // Input muy lento, probablemente es escritura manual
                buffer = e.key && e.key.length === 1 ? e.key : '';
            }
        }, true); // Usar capture para interceptar antes
    },
    
    /**
     * Inicializa los sonidos de feedback
     */
    _initSounds: function() {
        // Crear contexto de audio
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContext();
            
            // Sonido de éxito (beep corto agudo)
            this.sounds.success = this._createBeep(880, 0.1, 'sine');
            
            // Sonido de error (beep más grave y largo)
            this.sounds.error = this._createBeep(220, 0.3, 'sawtooth');
            
            // Sonido de escaneo (beep medio)
            this.sounds.scan = this._createBeep(660, 0.05, 'sine');
            
        } catch (e) {
            console.warn('Audio no disponible:', e);
            this.config.enableSound = false;
        }
    },
    
    /**
     * Crea un generador de beep
     */
    _createBeep: function(frequency, duration, type) {
        const self = this;
        return function() {
            if (!self.config.enableSound || !self.audioContext) return;
            
            try {
                const oscillator = self.audioContext.createOscillator();
                const gainNode = self.audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(self.audioContext.destination);
                
                oscillator.frequency.value = frequency;
                oscillator.type = type;
                
                gainNode.gain.setValueAtTime(0.3, self.audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, self.audioContext.currentTime + duration);
                
                oscillator.start(self.audioContext.currentTime);
                oscillator.stop(self.audioContext.currentTime + duration);
            } catch (e) {
                // Silenciar errores de audio
            }
        };
    },
    
    /**
     * Inicializa elementos de feedback visual
     */
    _initVisualFeedback: function() {
        // Crear overlay de escaneo si no existe
        if (!document.getElementById('scan-feedback-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'scan-feedback-overlay';
            overlay.innerHTML = `
                <div class="scan-feedback-content">
                    <div class="scan-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
                            <path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
                            <path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
                            <path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
                            <line x1="7" y1="12" x2="17" y2="12"></line>
                        </svg>
                    </div>
                    <div class="scan-serial"></div>
                    <div class="scan-status"></div>
                </div>
            `;
            document.body.appendChild(overlay);
            
            // Estilos
            const style = document.createElement('style');
            style.textContent = `
                #scan-feedback-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    display: none;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                    opacity: 0;
                    transition: opacity 0.2s ease;
                }
                #scan-feedback-overlay.visible {
                    display: flex;
                    opacity: 1;
                }
                #scan-feedback-overlay .scan-feedback-content {
                    background: white;
                    padding: 2rem 3rem;
                    border-radius: 1rem;
                    text-align: center;
                    max-width: 90%;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    transform: scale(0.9);
                    transition: transform 0.2s ease;
                }
                #scan-feedback-overlay.visible .scan-feedback-content {
                    transform: scale(1);
                }
                #scan-feedback-overlay .scan-icon {
                    color: #6366f1;
                    margin-bottom: 1rem;
                    animation: pulse 1s infinite;
                }
                #scan-feedback-overlay.success .scan-icon {
                    color: #10b981;
                    animation: none;
                }
                #scan-feedback-overlay.error .scan-icon {
                    color: #ef4444;
                    animation: shake 0.5s;
                }
                #scan-feedback-overlay .scan-serial {
                    font-size: 1.5rem;
                    font-weight: bold;
                    font-family: monospace;
                    color: #1f2937;
                    margin-bottom: 0.5rem;
                    word-break: break-all;
                }
                #scan-feedback-overlay .scan-status {
                    font-size: 1rem;
                    color: #6b7280;
                }
                #scan-feedback-overlay.success .scan-status {
                    color: #10b981;
                }
                #scan-feedback-overlay.error .scan-status {
                    color: #ef4444;
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-10px); }
                    75% { transform: translateX(10px); }
                }
            `;
            document.head.appendChild(style);
        }
    },
    
    // ============================================
    // MANEJO DE ESCANEO
    // ============================================
    
    /**
     * Maneja un escaneo detectado
     * @param {string} code - Código escaneado
     */
    _handleScan: function(code) {
        const self = this;
        
        // Normalizar código
        code = code.trim().toUpperCase();
        
        if (code.length < this.config.minCodeLength) {
            return;
        }
        
        console.log('📷 Código escaneado:', code);
        
        // Actualizar estado
        this.state.lastScan = {
            code: code,
            timestamp: new Date(),
            mode: this.state.currentMode
        };
        this.state.scanCount++;
        
        // Reproducir sonido de escaneo
        if (this.sounds.scan) this.sounds.scan();
        
        // Mostrar feedback visual
        this._showScanFeedback(code, 'Procesando...', 'scanning');
        
        // Ejecutar callback según el modo
        if (this.state.callbacks.onScan) {
            this.state.callbacks.onScan(code, this.state.currentMode);
        }
        
        // Validar con el servidor
        this._validateSerial(code)
            .then(result => {
                if (result.success) {
                    self._showScanFeedback(code, result.message || 'Serial válido', 'success');
                    if (self.sounds.success) self.sounds.success();
                    
                    if (self.state.callbacks.onValid) {
                        self.state.callbacks.onValid(code, result);
                    }
                    
                    // Si hay un input objetivo, escribir el código
                    if (self.state.targetInput) {
                        self.state.targetInput.value = code;
                        self.state.targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                } else {
                    self._showScanFeedback(code, result.message || 'Serial no válido', 'error');
                    if (self.sounds.error) self.sounds.error();
                    
                    if (self.state.callbacks.onInvalid) {
                        self.state.callbacks.onInvalid(code, result);
                    }
                }
            })
            .catch(error => {
                self._showScanFeedback(code, 'Error de conexión', 'error');
                if (self.sounds.error) self.sounds.error();
                
                if (self.state.callbacks.onError) {
                    self.state.callbacks.onError(code, error);
                }
            });
    },
    
    /**
     * Maneja un posible escaneo (sin sufijo confirmado)
     */
    _handlePossibleScan: function(code) {
        // Solo procesar si parece un serial válido
        if (/^[A-Z0-9\-_.]+$/i.test(code)) {
            this._handleScan(code);
        }
    },
    
    /**
     * Muestra feedback visual del escaneo
     */
    _showScanFeedback: function(code, status, type) {
        if (!this.config.enableVisualFeedback) return;
        
        const overlay = document.getElementById('scan-feedback-overlay');
        if (!overlay) return;
        
        const serialEl = overlay.querySelector('.scan-serial');
        const statusEl = overlay.querySelector('.scan-status');
        
        serialEl.textContent = code;
        statusEl.textContent = status;
        
        overlay.className = 'visible ' + type;
        
        // Auto-ocultar después de un tiempo
        clearTimeout(this._feedbackTimeout);
        this._feedbackTimeout = setTimeout(() => {
            overlay.classList.remove('visible');
        }, type === 'scanning' ? 5000 : 2000);
    },
    
    /**
     * Valida un serial con el servidor
     */
    _validateSerial: function(code) {
        return fetch(this.config.searchEndpoint + '?q=' + encodeURIComponent(code), {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.found && data.serial) {
                return {
                    success: true,
                    serial: data.serial,
                    message: `${data.serial.laptop?.display_name || 'Producto encontrado'}\nEstado: ${data.serial.status_display}`
                };
            } else {
                return {
                    success: false,
                    message: 'Serial no encontrado en el sistema'
                };
            }
        });
    },
    
    // ============================================
    // API PÚBLICA
    // ============================================
    
    /**
     * Establece el modo de escaneo actual
     * @param {string} mode - 'search', 'add', 'sell'
     */
    setMode: function(mode) {
        this.state.currentMode = mode;
        console.log('📱 Modo de escaneo:', mode);
    },
    
    /**
     * Establece el input donde escribir el código escaneado
     * @param {HTMLElement|string} input - Input o selector
     */
    setTargetInput: function(input) {
        if (typeof input === 'string') {
            input = document.querySelector(input);
        }
        this.state.targetInput = input;
    },
    
    /**
     * Registra callbacks para eventos de escaneo
     * @param {string} event - 'scan', 'valid', 'invalid', 'error'
     * @param {Function} callback - Función a ejecutar
     */
    on: function(event, callback) {
        const eventMap = {
            'scan': 'onScan',
            'valid': 'onValid',
            'invalid': 'onInvalid',
            'error': 'onError'
        };
        
        if (eventMap[event]) {
            this.state.callbacks[eventMap[event]] = callback;
        }
    },
    
    /**
     * Simula un escaneo (útil para testing)
     * @param {string} code - Código a simular
     */
    simulate: function(code) {
        this._handleScan(code);
    },
    
    /**
     * Habilita/deshabilita sonidos
     * @param {boolean} enabled
     */
    setSoundEnabled: function(enabled) {
        this.config.enableSound = enabled;
    },
    
    /**
     * Habilita/deshabilita feedback visual
     * @param {boolean} enabled
     */
    setVisualFeedbackEnabled: function(enabled) {
        this.config.enableVisualFeedback = enabled;
    },
    
    /**
     * Obtiene estadísticas de escaneo
     */
    getStats: function() {
        return {
            scanCount: this.state.scanCount,
            lastScan: this.state.lastScan,
            currentMode: this.state.currentMode,
            isInitialized: this.state.isInitialized
        };
    },
    
    /**
     * Resetea el contador de escaneos
     */
    resetStats: function() {
        this.state.scanCount = 0;
        this.state.lastScan = null;
    }
};

// ============================================
// COMPONENTE: INPUT DE SERIAL CON ESCANEO
// ============================================

/**
 * Componente de input especializado para seriales
 * Incluye botón de escaneo y validación en tiempo real
 */
class SerialInput {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Contenedor no encontrado:', containerId);
            return;
        }
        
        this.options = {
            placeholder: 'Escanear o escribir serial...',
            validateOnInput: true,
            showScanButton: true,
            allowMultiple: false,
            onSerialAdded: null,
            onSerialRemoved: null,
            onValidate: null,
            ...options
        };
        
        this.serials = [];
        this._render();
        this._attachEvents();
    }
    
    _render() {
        this.container.innerHTML = `
            <div class="serial-input-wrapper">
                <div class="serial-input-field">
                    <input type="text" 
                           class="serial-text-input form-input" 
                           placeholder="${this.options.placeholder}"
                           autocomplete="off"
                           spellcheck="false">
                    ${this.options.showScanButton ? `
                        <button type="button" class="serial-scan-btn" title="Activar escáner">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
                                <path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
                                <path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
                                <path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
                                <line x1="7" y1="12" x2="17" y2="12"></line>
                            </svg>
                        </button>
                    ` : ''}
                </div>
                <div class="serial-validation-status"></div>
                <div class="serial-list"></div>
            </div>
        `;
        
        this.input = this.container.querySelector('.serial-text-input');
        this.scanBtn = this.container.querySelector('.serial-scan-btn');
        this.statusEl = this.container.querySelector('.serial-validation-status');
        this.listEl = this.container.querySelector('.serial-list');
        
        // Agregar estilos si no existen
        if (!document.getElementById('serial-input-styles')) {
            const style = document.createElement('style');
            style.id = 'serial-input-styles';
            style.textContent = `
                .serial-input-wrapper {
                    width: 100%;
                }
                .serial-input-field {
                    position: relative;
                    display: flex;
                    gap: 0.5rem;
                }
                .serial-text-input {
                    flex: 1;
                    font-family: monospace;
                    text-transform: uppercase;
                }
                .serial-scan-btn {
                    padding: 0.5rem 0.75rem;
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    color: white;
                    border: none;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .serial-scan-btn:hover {
                    transform: scale(1.05);
                    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
                }
                .serial-scan-btn.active {
                    animation: pulse 1s infinite;
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                }
                .serial-validation-status {
                    font-size: 0.875rem;
                    margin-top: 0.25rem;
                    min-height: 1.25rem;
                }
                .serial-validation-status.valid {
                    color: #10b981;
                }
                .serial-validation-status.invalid {
                    color: #ef4444;
                }
                .serial-validation-status.loading {
                    color: #6b7280;
                }
                .serial-list {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                    margin-top: 0.5rem;
                }
                .serial-tag {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.25rem 0.75rem;
                    background: #e0e7ff;
                    color: #4338ca;
                    border-radius: 9999px;
                    font-size: 0.875rem;
                    font-family: monospace;
                }
                .serial-tag button {
                    background: none;
                    border: none;
                    color: inherit;
                    cursor: pointer;
                    padding: 0;
                    opacity: 0.7;
                }
                .serial-tag button:hover {
                    opacity: 1;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    _attachEvents() {
        const self = this;
        
        // Input manual
        this.input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                self._processInput();
            }
        });
        
        // Validación en tiempo real
        if (this.options.validateOnInput) {
            let debounceTimer;
            this.input.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    self._validateInput();
                }, 500);
            });
        }
        
        // Botón de escaneo
        if (this.scanBtn) {
            this.scanBtn.addEventListener('click', function() {
                self._toggleScanMode();
            });
        }
        
        // Registrar con BarcodeScanner global
        if (typeof BarcodeScanner !== 'undefined' && BarcodeScanner.state.isInitialized) {
            BarcodeScanner.on('valid', function(code, result) {
                self.addSerial(code, result.serial);
            });
        }
    }
    
    _processInput() {
        const value = this.input.value.trim().toUpperCase();
        if (value) {
            this.addSerial(value);
            this.input.value = '';
        }
    }
    
    _validateInput() {
        const value = this.input.value.trim();
        if (value.length < 3) {
            this.statusEl.textContent = '';
            this.statusEl.className = 'serial-validation-status';
            return;
        }
        
        this.statusEl.textContent = 'Validando...';
        this.statusEl.className = 'serial-validation-status loading';
        
        // Aquí irá la validación con el servidor
        fetch(`/api/serials/search?q=${encodeURIComponent(value)}`)
            .then(r => r.json())
            .then(data => {
                if (data.found) {
                    this.statusEl.textContent = `✓ ${data.serial.laptop?.display_name || 'Encontrado'}`;
                    this.statusEl.className = 'serial-validation-status valid';
                } else {
                    this.statusEl.textContent = 'Serial no encontrado';
                    this.statusEl.className = 'serial-validation-status invalid';
                }
            })
            .catch(() => {
                this.statusEl.textContent = '';
                this.statusEl.className = 'serial-validation-status';
            });
    }
    
    _toggleScanMode() {
        if (this.scanBtn.classList.contains('active')) {
            this.scanBtn.classList.remove('active');
            BarcodeScanner.setTargetInput(null);
        } else {
            this.scanBtn.classList.add('active');
            BarcodeScanner.setTargetInput(this.input);
            this.input.focus();
        }
    }
    
    addSerial(serial, data = null) {
        if (!serial) return;
        
        serial = serial.trim().toUpperCase();
        
        // Verificar duplicados
        if (this.serials.find(s => s.serial === serial)) {
            return;
        }
        
        // Si no permite múltiples, limpiar lista
        if (!this.options.allowMultiple) {
            this.serials = [];
        }
        
        this.serials.push({ serial, data });
        this._renderList();
        
        if (this.options.onSerialAdded) {
            this.options.onSerialAdded(serial, data);
        }
    }
    
    removeSerial(serial) {
        const index = this.serials.findIndex(s => s.serial === serial);
        if (index > -1) {
            this.serials.splice(index, 1);
            this._renderList();
            
            if (this.options.onSerialRemoved) {
                this.options.onSerialRemoved(serial);
            }
        }
    }
    
    _renderList() {
        this.listEl.innerHTML = this.serials.map(s => `
            <span class="serial-tag">
                ${s.serial}
                <button type="button" onclick="this.parentElement.remove()" data-serial="${s.serial}">×</button>
            </span>
        `).join('');
        
        // Agregar eventos de eliminación
        this.listEl.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', () => {
                this.removeSerial(btn.dataset.serial);
            });
        });
    }
    
    getSerials() {
        return this.serials.map(s => s.serial);
    }
    
    clear() {
        this.serials = [];
        this.input.value = '';
        this._renderList();
        this.statusEl.textContent = '';
    }
}

// ============================================
// AUTO-INICIALIZACIÓN
// ============================================

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si hay elementos de serial en la página
    if (document.querySelector('[data-barcode-scanner]') || 
        document.querySelector('.serial-input-container')) {
        BarcodeScanner.init();
    }
});

// Exportar para uso global
window.BarcodeScanner = BarcodeScanner;
window.SerialInput = SerialInput;
