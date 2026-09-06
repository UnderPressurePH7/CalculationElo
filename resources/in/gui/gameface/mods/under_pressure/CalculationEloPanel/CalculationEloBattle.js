(function () {
    'use strict';

    var root = document.getElementById('elo-root');
    var namesEl = document.getElementById('elo-names');
    var alliesNameEl = document.getElementById('elo-allies-name');
    var enemiesNameEl = document.getElementById('elo-enemies-name');
    var ratingsEl = document.getElementById('elo-ratings');
    var alliesRatingEl = document.getElementById('elo-allies-rating');
    var enemiesRatingEl = document.getElementById('elo-enemies-rating');
    var changesEl = document.getElementById('elo-changes');
    var gainEl = document.getElementById('elo-gain');
    var lossEl = document.getElementById('elo-loss');
    var statsEl = document.getElementById('elo-stats');
    var battlesEl = document.getElementById('elo-battles');
    var winrateEl = document.getElementById('elo-winrate');
    var statsSeparatorEl = document.getElementById('elo-stats-separator');

    var POLL_FAST = 200;
    var POLL_SLOW = 1000;

    var lastPayload = null;
    var lastReportedSize = null;
    var payload = {};
    var applied = {};
    var layoutDirty = false;
    var needsMeasure = true;

    var renderPending = false;
    var renderHandle = 0;
    var usesRaf = typeof requestAnimationFrame === 'function';
    var pendingSelfResize = false;
    var lastRemScale = 0;

    var dataEventSeen = false;
    var pollIntervalId = 0;

    function sendCmd(name, value) {
        try {
            if (window.model && typeof window.model.onCmd === 'function') {
                window.model.onCmd({
                    name: String(name),
                    value: value === undefined ? '' : String(value)
                });
            }
        } catch (e) {}
    }

    function toInt(value, fallback) {
        var parsed = parseInt(value, 10);
        return isNaN(parsed) ? fallback : parsed;
    }

    function toNumber(value, fallback) {
        var parsed = parseFloat(value);
        return isNaN(parsed) ? fallback : parsed;
    }

    function color(value, fallback) {
        value = value || fallback || 'FFFFFF';
        return '#' + String(value).replace('#', '');
    }

    function truncateName(value) {
        value = value ? String(value) : ' ';
        if (value === 'Unknown' || value === ' ') {
            return ' ';
        }
        value = value.toUpperCase();
        return value.length > 6 ? value.substr(0, 6) : value;
    }

    function winrateColor(value) {
        if (value >= 75) return '#D042F3';
        if (value >= 65) return '#02C9B3';
        if (value >= 58) return '#60FF00';
        if (value >= 50) return '#F8F400';
        if (value >= 40) return '#FE7903';
        if (value >= 30) return '#FE0E00';
        return '#FFFFFF';
    }

    function battlesColor(value) {
        if (value >= 800) return '#D042F3';
        if (value >= 500) return '#02C9B3';
        if (value >= 400) return '#60FF00';
        if (value >= 350) return '#F8F400';
        return '#FFFFFF';
    }

    function formatWinrate(value) {
        return Math.round(value) + '%';
    }

    function setText(el, key, value) {
        if (applied[key] === value) {
            return;
        }
        applied[key] = value;
        el.textContent = value;
        layoutDirty = true;
    }

    function setColor(el, key, value) {
        if (applied[key] === value) {
            return;
        }
        applied[key] = value;
        el.style.color = value;
    }

    function setVisible(el, key, visible) {
        if (applied[key] === visible) {
            return;
        }
        applied[key] = visible;
        el.style.display = visible ? '' : 'none';
        layoutDirty = true;
    }

    function setFontSize(value) {
        if (applied.fontSize === value) {
            return;
        }
        applied.fontSize = value;
        document.documentElement.style.fontSize = value + 'px';
        layoutDirty = true;
    }

    function setPanelHidden(hidden) {
        if (applied.hidden === hidden) {
            return;
        }
        applied.hidden = hidden;
        if (hidden) {
            root.classList.add('elo-hidden');
        } else {
            root.classList.remove('elo-hidden');
        }
    }

    function clientSize() {
        try {
            if (window.viewEnv && viewEnv.getClientSizePx) {
                var s = viewEnv.getClientSizePx();
                if (s && s.width > 0 && s.height > 0) {
                    return { width: s.width, height: s.height };
                }
            }
        } catch (e) {}
        return {
            width: document.documentElement.clientWidth || window.innerWidth || 1920,
            height: document.documentElement.clientHeight || window.innerHeight || 1080
        };
    }

    function remScale(payloadScale) {
        var uiScale = toNumber(payloadScale, 1) || 1;
        try {
            if (window.viewEnv && viewEnv.remToPx) {
                var px = viewEnv.remToPx(1);
                if (px > 0) return px;
            }
        } catch (e) {}
        if (pendingSelfResize && lastRemScale > 0) {
            return lastRemScale;
        }
        var size = clientSize();
        var responsive = Math.min(size.width / 1920, size.height / 1080) || 1;
        return responsive * uiScale;
    }

    function reportSize(width, height) {
        var w = Math.max(1, Math.round(width));
        var h = Math.max(1, Math.round(height));
        var key = w + 'x' + h;
        if (key === lastReportedSize) {
            return;
        }
        try {
            if (window.viewEnv && viewEnv.resizeViewPx) {
                lastReportedSize = key;
                pendingSelfResize = true;
                viewEnv.resizeViewPx(w, h);
                sendCmd('onSize', key);
            }
        } catch (e) {}
    }

    function readPayload() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw === lastPayload) {
            return false;
        }
        lastPayload = raw;
        try {
            payload = JSON.parse(raw || '{}');
        } catch (e) {
            payload = {};
        }
        return true;
    }

    function render() {
        var cfg = payload.config || {};
        var state = payload.state || {};

        layoutDirty = false;

        var scale = remScale(payload.scale);
        lastRemScale = scale;
        setFontSize(scale);

        setPanelHidden(payload.visible === false);

        setVisible(namesEl, 'namesRow', cfg.showTeamNames !== false);
        setText(alliesNameEl, 'alliesName', truncateName(state.allies_name));
        setText(enemiesNameEl, 'enemiesName', truncateName(state.enemies_name));
        setColor(alliesNameEl, 'alliesNameColor', color(cfg.alliesNamesColor, '4F8627'));
        setColor(enemiesNameEl, 'enemiesNameColor', color(cfg.enemiesNamesColor, '9A0101'));

        var alliesRating = toInt(state.allies_rating, 0);
        var enemiesRating = toInt(state.enemies_rating, 0);
        setText(alliesRatingEl, 'alliesRating', alliesRating > 0 ? String(alliesRating) : ' ');
        setText(enemiesRatingEl, 'enemiesRating', enemiesRating > 0 ? String(enemiesRating) : ' ');
        setColor(alliesRatingEl, 'alliesRatingColor', color(cfg.alliesRatingColor, '4F8627'));
        setColor(enemiesRatingEl, 'enemiesRatingColor', color(cfg.enemiesRatingColor, '9A0101'));

        setVisible(changesEl, 'changesRow', cfg.showEloChanges !== false);
        var gain = toInt(state.elo_plus, 0);
        var loss = toInt(state.elo_minus, 0);
        setText(gainEl, 'gain', gain > 0 ? '+' + gain : '');
        setText(lossEl, 'loss', loss < 0 ? String(loss) : '');
        setColor(gainEl, 'gainColor', color(cfg.eloGainColor, '00FF00'));
        setColor(lossEl, 'lossColor', color(cfg.eloLossColor, 'FF0000'));

        setVisible(statsEl, 'statsRow', cfg.showWinrateAndBattles !== false);
        var battles = toInt(state.battles_count, 0);
        var winrate = toNumber(state.wins_percent, 0);
        var hasStats = battles > 0 || winrate > 0;
        setText(winrateEl, 'winrate', hasStats ? formatWinrate(winrate) : '');
        setText(statsSeparatorEl, 'separator', hasStats ? '|' : '');
        setText(battlesEl, 'battles', hasStats ? String(battles) : '');
        setColor(winrateEl, 'winrateColor', winrateColor(winrate));
        setColor(battlesEl, 'battlesColor', battlesColor(battles));

        pendingSelfResize = false;

        if (layoutDirty || needsMeasure) {
            layoutDirty = false;
            needsMeasure = false;
            var rect = root.getBoundingClientRect();
            reportSize(rect.width, rect.height);
        }
    }

    function runRender() {
        renderPending = false;
        renderHandle = 0;
        render();
    }

    function scheduleRender() {
        if (renderPending) {
            return;
        }
        renderPending = true;
        if (usesRaf) {
            renderHandle = requestAnimationFrame(runRender);
        } else {
            renderHandle = window.setTimeout(runRender, 16);
        }
    }

    function onModelChanged() {
        if (readPayload()) {
            scheduleRender();
        }
    }

    function onDataChanged() {
        if (!dataEventSeen) {
            dataEventSeen = true;
            restartPoll(POLL_SLOW);
        }
        onModelChanged();
    }

    function onEnvChanged() {
        needsMeasure = true;
        scheduleRender();
    }

    function poll() {
        onModelChanged();
    }

    function restartPoll(interval) {
        try {
            if (pollIntervalId) {
                window.clearInterval(pollIntervalId);
            }
            pollIntervalId = window.setInterval(poll, interval);
        } catch (e) {}
    }

    function shutdown() {
        try {
            if (pollIntervalId) {
                window.clearInterval(pollIntervalId);
                pollIntervalId = 0;
            }
        } catch (e) {}
        try {
            if (renderHandle) {
                if (usesRaf) {
                    cancelAnimationFrame(renderHandle);
                } else {
                    window.clearTimeout(renderHandle);
                }
                renderHandle = 0;
                renderPending = false;
            }
        } catch (e) {}
    }

    function initialize() {
        readPayload();
        render();
        if (window.engine) {
            window.engine.on('viewEnv.onDataChanged', onDataChanged);
            window.engine.on('self.onScaleUpdated', onEnvChanged);
            window.engine.on('clientResized', onEnvChanged);
        }
        if (window.viewEnv && typeof viewEnv.addDataChangedCallback === 'function') {
            try {
                viewEnv.addDataChangedCallback('model', 0, true);
            } catch (e) {}
        }
        try {
            window.addEventListener('resize', onEnvChanged);
            window.addEventListener('unload', shutdown);
        } catch (e) {}
        restartPoll(POLL_FAST);
        if (window.model && typeof window.model.onReady === 'function') {
            window.model.onReady({});
        }
    }

    function afterFrames() {
        requestAnimationFrame(function () {
            requestAnimationFrame(initialize);
        });
    }

    if (window.engine && window.engine.whenReady) {
        var domReady = window.isDomBuilt ? Promise.resolve() : new Promise(function (resolve) {
            window.engine.on('self.onDomBuilt', resolve);
        });
        Promise.all([window.engine.whenReady, domReady]).then(afterFrames);
    } else {
        afterFrames();
    }
}());
