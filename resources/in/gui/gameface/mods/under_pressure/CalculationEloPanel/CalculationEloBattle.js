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

    var lastPayload = null;
    var lastReportedSize = null;
    var payload = {};

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

    function setVisible(el, visible) {
        el.style.display = visible ? '' : 'none';
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
                viewEnv.resizeViewPx(w, h);
                lastReportedSize = key;
                sendCmd('onSize', key);
            }
        } catch (e) {}
    }

    function readPayload() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw === lastPayload) {
            return;
        }
        lastPayload = raw;
        try {
            payload = JSON.parse(raw || '{}');
        } catch (e) {
            payload = {};
        }
    }

    function render() {
        readPayload();
        var cfg = payload.config || {};
        var state = payload.state || {};
        var scale = remScale(payload.scale);

        document.documentElement.style.fontSize = scale + 'px';

        if (payload.visible === false) {
            root.classList.add('elo-hidden');
        } else {
            root.classList.remove('elo-hidden');
        }

        setVisible(namesEl, cfg.showTeamNames !== false);
        alliesNameEl.textContent = truncateName(state.allies_name);
        enemiesNameEl.textContent = truncateName(state.enemies_name);
        alliesNameEl.style.color = color(cfg.alliesNamesColor, '4F8627');
        enemiesNameEl.style.color = color(cfg.enemiesNamesColor, '9A0101');

        var alliesRating = toInt(state.allies_rating, 0);
        var enemiesRating = toInt(state.enemies_rating, 0);
        alliesRatingEl.textContent = alliesRating > 0 ? String(alliesRating) : ' ';
        enemiesRatingEl.textContent = enemiesRating > 0 ? String(enemiesRating) : ' ';
        alliesRatingEl.style.color = color(cfg.alliesRatingColor, '4F8627');
        enemiesRatingEl.style.color = color(cfg.enemiesRatingColor, '9A0101');

        setVisible(changesEl, cfg.showEloChanges !== false);
        var gain = toInt(state.elo_plus, 0);
        var loss = toInt(state.elo_minus, 0);
        gainEl.textContent = gain > 0 ? '+' + gain : '';
        lossEl.textContent = loss < 0 ? String(loss) : '';
        gainEl.style.color = color(cfg.eloGainColor, '00FF00');
        lossEl.style.color = color(cfg.eloLossColor, 'FF0000');

        setVisible(statsEl, cfg.showWinrateAndBattles !== false);
        var battles = toInt(state.battles_count, 0);
        var winrate = toNumber(state.wins_percent, 0);
        var hasStats = battles > 0 || winrate > 0;
        winrateEl.textContent = hasStats ? formatWinrate(winrate) : '';
        statsSeparatorEl.textContent = hasStats ? '|' : '';
        battlesEl.textContent = hasStats ? String(battles) : '';
        winrateEl.style.color = winrateColor(winrate);
        battlesEl.style.color = battlesColor(battles);

        var rect = root.getBoundingClientRect();
        reportSize(rect.width, rect.height);
    }

    function poll() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw !== lastPayload) {
            render();
        }
    }

    function initialize() {
        render();
        if (window.engine) {
            window.engine.on('viewEnv.onDataChanged', render);
            window.engine.on('self.onScaleUpdated', render);
            window.engine.on('clientResized', render);
        }
        if (window.viewEnv && typeof viewEnv.addDataChangedCallback === 'function') {
            try {
                viewEnv.addDataChangedCallback('model', 0, true);
            } catch (e) {}
        }
        try {
            window.addEventListener('resize', render);
        } catch (e) {}
        window.setInterval(poll, 200);
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
