/**
 * FlowMate Theme & Atmosphere Management System
 * Liquid Glass UI System (Nature, Abstract, Architecture, Dark Serenity, Gaming, Synthwave)
 * 
 * Supports:
 * - 6 Atmospheric Themes: nature, abstract, architecture, dark-serenity, gaming, synthwave
 * - 2 Modes: dark, light
 * - 2 Wallpapers per theme + custom user-uploaded wallpaper
 * - Visual Atmosphere Controls: Wallpaper Blur, Dimming, Glass Intensity, Solid Color Mode
 * - 3 Adaptive Focus Environments: Deep Study, Reading & Research, Recovery & Break
 * 
 * Vanilla JS, no ES modules, zero external dependencies.
 */

(function (window, document) {
    'use strict';

    // Storage keys
    const STORAGE_KEY_THEME = 'fm_theme';
    const STORAGE_KEY_MODE = 'fm_mode';
    const STORAGE_KEY_WALLPAPER = 'fm_wallpaper';
    const STORAGE_KEY_CUSTOM_WP = 'fm_custom_wallpaper';
    const STORAGE_KEY_BLUR = 'fm_wallpaper_blur';
    const STORAGE_KEY_DIM = 'fm_wallpaper_dim';
    const STORAGE_KEY_GLASS = 'fm_glass_intensity';
    const STORAGE_KEY_SOLID = 'fm_solid_color';
    const STORAGE_KEY_FOCUS_ENV = 'fm_focus_env';
    const STORAGE_KEY_LEGACY = 'flowmate_theme';

    // Themes metadata
    const THEMES = [
        {
            id: 'nature',
            name: 'Forest Focus',
            category: 'Nature',
            description: 'Tranquil canopy and organic sage tones for sustained calm',
            accentDark: '#10b981',
            accentLight: '#059669'
        },
        {
            id: 'abstract',
            name: 'Pure Form',
            category: 'Abstract',
            description: 'Minimal graphite depth and sculptural light composition',
            accentDark: '#8080ff',
            accentLight: '#5555cc'
        },
        {
            id: 'architecture',
            name: 'Minimal Atrium',
            category: 'Architecture',
            description: 'Sunlit stone, clean geometric planes and quiet structure',
            accentDark: '#e2b17a',
            accentLight: '#c2894b'
        },
        {
            id: 'dark-serenity',
            name: 'Dark Serenity',
            category: 'Atmospheric',
            description: 'Ultra-deep midnight obsidian with soft charcoal tranquility',
            accentDark: '#38bdf8',
            accentLight: '#0284c7'
        },
        {
            id: 'gaming',
            name: 'Electric Flow',
            category: 'Dynamic',
            description: 'High-focus cyber cyan with tactical contrast',
            accentDark: '#00c8ff',
            accentLight: '#0070cc'
        },
        {
            id: 'synthwave',
            name: 'Night Signal',
            category: 'Dynamic',
            description: 'Retro-futuristic dusk violet and subtle ambient glow',
            accentDark: '#c03aff',
            accentLight: '#8820cc'
        }
    ];

    // Wallpapers metadata per theme
    const WALLPAPERS = {
        nature: [
            { id: 1, name: 'Morning Mist', desc: 'Soft dawn canopy light with organic depth' },
            { id: 2, name: 'Forest Depth', desc: 'Tranquil emerald and shadowed moss gradients' }
        ],
        abstract: [
            { id: 1, name: 'Graphite', desc: 'Clean architectural charcoal and glass layers' },
            { id: 2, name: 'Deep Form', desc: 'Subtle monochromatic obsidian curvatures' }
        ],
        architecture: [
            { id: 1, name: 'Sunlit Atrium', desc: 'Warm limestone texture with ambient skylight' },
            { id: 2, name: 'Quiet Concrete', desc: 'Brutalist minimal stone with neutral shadow' }
        ],
        'dark-serenity': [
            { id: 1, name: 'Midnight Obsidian', desc: 'Pure low-stimulation deep navy tranquility' },
            { id: 2, name: 'Charcoal Slumber', desc: 'Restful graphite dusk for intense night study' }
        ],
        gaming: [
            { id: 1, name: 'Electric Night', desc: 'High-contrast cyber blue and ambient glow' },
            { id: 2, name: 'Digital Void', desc: 'Ultra-deep tactical midnight with pulse accents' }
        ],
        synthwave: [
            { id: 1, name: 'Violet Horizon', desc: 'Vibrant magenta and dusk violet gradients' },
            { id: 2, name: 'Neon Dawn', desc: 'Electric retro sunset with warm laser hues' }
        ]
    };

    const VALID_THEMES = ['nature', 'abstract', 'architecture', 'dark-serenity', 'gaming', 'synthwave'];
    const VALID_MODES = ['dark', 'light'];
    const VALID_GLASS = ['subtle', 'balanced', 'pronounced'];
    const VALID_FOCUS_ENVS = ['deep-study', 'reading', 'break'];

    // Internal reactive state
    let _theme = 'abstract';
    let _mode = 'dark';
    let _wallpaper = 1;
    let _customWallpaper = '';
    let _blur = 0; // px (0 to 40)
    let _dim = 0; // % (0 to 80)
    let _glass = 'balanced'; // 'subtle' | 'balanced' | 'pronounced'
    let _solidColor = false; // boolean
    let _focusEnv = 'deep-study'; // 'deep-study' | 'reading' | 'break'

    function storageGet(key, fallback) {
        try {
            const val = localStorage.getItem(key);
            return val !== null ? val : fallback;
        } catch (e) {
            console.warn('[ThemeManager] LocalStorage read failed:', e);
            return fallback;
        }
    }

    function storageSet(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (e) {
            console.warn('[ThemeManager] LocalStorage write failed:', e);
        }
    }

    /**
     * Apply all theme and atmosphere variables to the DOM
     */
    function apply() {
        const root = document.documentElement;
        if (root) {
            root.setAttribute('data-theme', _theme);
            root.setAttribute('data-mode', _mode);
            root.setAttribute('data-glass', _glass);
            root.setAttribute('data-focus-env', _focusEnv);
            root.style.setProperty('--wallpaper-blur', `${_blur}px`);
            root.style.setProperty('--wallpaper-dim', `${_dim / 100}`);

            if (_customWallpaper) {
                root.style.setProperty('--custom-wallpaper-url', `url("${_customWallpaper}")`);
                root.setAttribute('data-wallpaper-custom', 'true');
            } else {
                root.style.removeProperty('--custom-wallpaper-url');
                root.removeAttribute('data-wallpaper-custom');
            }

            if (_solidColor) {
                root.setAttribute('data-solid-color', 'true');
            } else {
                root.removeAttribute('data-solid-color');
            }
        }

        if (document.body) {
            document.body.setAttribute('data-wallpaper', String(_wallpaper));
            document.body.classList.remove('theme-dark', 'theme-light');
            document.body.classList.add(_mode === 'light' ? 'theme-light' : 'theme-dark');
        }

        updateThemeIcon();
        syncAppState();
    }

    function updateThemeIcon() {
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = _mode === 'light' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
    }

    function dispatchChangeEvent() {
        const detail = ThemeManager.getPrefs();
        try {
            const event = new CustomEvent('flowmate:themechange', {
                detail: detail,
                bubbles: true,
                cancelable: false
            });
            document.dispatchEvent(event);
        } catch (e) {
            const event = document.createEvent('CustomEvent');
            event.initCustomEvent('flowmate:themechange', true, false, detail);
            document.dispatchEvent(event);
        }
    }

    function syncAppState() {
        if (typeof window.AppState !== 'undefined' && window.AppState) {
            window.AppState.theme = _mode;
            window.AppState.focusEnv = _focusEnv;
        }
    }

    function init() {
        _theme = VALID_THEMES.includes(storageGet(STORAGE_KEY_THEME, 'abstract')) ? storageGet(STORAGE_KEY_THEME, 'abstract') : 'abstract';
        
        let savedMode = storageGet(STORAGE_KEY_MODE, null);
        if (!savedMode || !VALID_MODES.includes(savedMode)) {
            savedMode = storageGet(STORAGE_KEY_LEGACY, 'dark');
        }
        _mode = VALID_MODES.includes(savedMode) ? savedMode : 'dark';

        _wallpaper = parseInt(storageGet(STORAGE_KEY_WALLPAPER, '1'), 10);
        if (_wallpaper !== 1 && _wallpaper !== 2) _wallpaper = 1;

        _customWallpaper = storageGet(STORAGE_KEY_CUSTOM_WP, '');
        _blur = parseInt(storageGet(STORAGE_KEY_BLUR, '0'), 10);
        if (isNaN(_blur) || _blur < 0 || _blur > 40) _blur = 0;

        _dim = parseInt(storageGet(STORAGE_KEY_DIM, '0'), 10);
        if (isNaN(_dim) || _dim < 0 || _dim > 80) _dim = 0;

        _glass = VALID_GLASS.includes(storageGet(STORAGE_KEY_GLASS, 'balanced')) ? storageGet(STORAGE_KEY_GLASS, 'balanced') : 'balanced';
        _solidColor = storageGet(STORAGE_KEY_SOLID, 'false') === 'true';
        _focusEnv = VALID_FOCUS_ENVS.includes(storageGet(STORAGE_KEY_FOCUS_ENV, 'deep-study')) ? storageGet(STORAGE_KEY_FOCUS_ENV, 'deep-study') : 'deep-study';

        if (document.documentElement) {
            document.documentElement.setAttribute('data-theme', _theme);
            document.documentElement.setAttribute('data-mode', _mode);
            document.documentElement.setAttribute('data-glass', _glass);
            document.documentElement.setAttribute('data-focus-env', _focusEnv);
        }

        if (document.body) {
            apply();
        } else {
            document.addEventListener('DOMContentLoaded', function () {
                apply();
            }, { once: true });
        }
    }

    // Public ThemeManager API
    const ThemeManager = {
        themes: THEMES,
        wallpapers: WALLPAPERS,

        setTheme: function (themeId) {
            if (!VALID_THEMES.includes(themeId)) {
                console.warn(`[ThemeManager] Unknown theme: "${themeId}".`);
                return this.getPrefs();
            }
            _theme = themeId;
            storageSet(STORAGE_KEY_THEME, _theme);
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setMode: function (mode) {
            if (!VALID_MODES.includes(mode)) {
                console.warn(`[ThemeManager] Unknown mode: "${mode}".`);
                return this.getPrefs();
            }
            _mode = mode;
            storageSet(STORAGE_KEY_MODE, _mode);
            storageSet(STORAGE_KEY_LEGACY, _mode);
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setWallpaper: function (wallpaperId) {
            const parsed = parseInt(wallpaperId, 10);
            if (parsed !== 1 && parsed !== 2) return this.getPrefs();
            _wallpaper = parsed;
            // Clear custom wallpaper when choosing a preset
            _customWallpaper = '';
            storageSet(STORAGE_KEY_CUSTOM_WP, '');
            storageSet(STORAGE_KEY_WALLPAPER, String(_wallpaper));
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setCustomWallpaper: function (dataUrl) {
            _customWallpaper = dataUrl || '';
            storageSet(STORAGE_KEY_CUSTOM_WP, _customWallpaper);
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setBlur: function (blurPx) {
            _blur = Math.max(0, Math.min(40, parseInt(blurPx, 10) || 0));
            storageSet(STORAGE_KEY_BLUR, String(_blur));
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setDim: function (dimPercent) {
            _dim = Math.max(0, Math.min(80, parseInt(dimPercent, 10) || 0));
            storageSet(STORAGE_KEY_DIM, String(_dim));
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setGlassIntensity: function (intensity) {
            if (!VALID_GLASS.includes(intensity)) return this.getPrefs();
            _glass = intensity;
            storageSet(STORAGE_KEY_GLASS, _glass);
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setSolidColor: function (isSolid) {
            _solidColor = Boolean(isSolid);
            storageSet(STORAGE_KEY_SOLID, String(_solidColor));
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        setFocusEnvironment: function (env) {
            if (!VALID_FOCUS_ENVS.includes(env)) return this.getPrefs();
            _focusEnv = env;
            storageSet(STORAGE_KEY_FOCUS_ENV, _focusEnv);
            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        resetDefaults: function () {
            _theme = 'abstract';
            _mode = 'dark';
            _wallpaper = 1;
            _customWallpaper = '';
            _blur = 0;
            _dim = 0;
            _glass = 'balanced';
            _solidColor = false;
            _focusEnv = 'deep-study';

            storageSet(STORAGE_KEY_THEME, _theme);
            storageSet(STORAGE_KEY_MODE, _mode);
            storageSet(STORAGE_KEY_WALLPAPER, '1');
            storageSet(STORAGE_KEY_CUSTOM_WP, '');
            storageSet(STORAGE_KEY_BLUR, '0');
            storageSet(STORAGE_KEY_DIM, '0');
            storageSet(STORAGE_KEY_GLASS, 'balanced');
            storageSet(STORAGE_KEY_SOLID, 'false');
            storageSet(STORAGE_KEY_FOCUS_ENV, 'deep-study');

            apply();
            dispatchChangeEvent();
            return this.getPrefs();
        },

        toggle: function () {
            const nextMode = _mode === 'light' ? 'dark' : 'light';
            this.setMode(nextMode);
            return nextMode;
        },

        getPrefs: function () {
            return {
                theme: _theme,
                mode: _mode,
                wallpaper: _wallpaper,
                customWallpaper: _customWallpaper,
                blur: _blur,
                dim: _dim,
                glass: _glass,
                solidColor: _solidColor,
                focusEnv: _focusEnv
            };
        },

        apply: apply,
        init: init
    };

    // Synchronously initialize attributes on load
    init();

    window.ThemeManager = ThemeManager;

    window.toggleTheme = function () {
        const newMode = ThemeManager.toggle();
        if (typeof window.Toast !== 'undefined' && window.Toast.show) {
            window.Toast.show(`Switched to ${newMode} theme`, 'info', 2000);
        }
        return newMode;
    };

    function bindAppStateShim() {
        if (window.AppState) {
            try {
                const descriptor = Object.getOwnPropertyDescriptor(window.AppState, 'theme');
                if (!descriptor || descriptor.configurable) {
                    Object.defineProperty(window.AppState, 'theme', {
                        get: function () { return ThemeManager.getPrefs().mode; },
                        set: function (newVal) {
                            if (newVal === 'dark' || newVal === 'light') ThemeManager.setMode(newVal);
                        },
                        configurable: true,
                        enumerable: true
                    });
                }
            } catch (e) {
                window.AppState.theme = ThemeManager.getPrefs().mode;
            }
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindAppStateShim);
    } else {
        bindAppStateShim();
    }

})(typeof window !== 'undefined' ? window : this, typeof document !== 'undefined' ? document : {});
