/**
 * A11y Enhancer — 捕获 A11y 语义并通过 Umami track API 发送
 * 替代独立的 RRWeb receiver，将结构化动作数据存入 Umami event_data
 *
 * 数据流:
 *   用户交互 → capture-phase 监听 → captureA11yContext → umami.track('a11y-action', {...})
 *                                            ↓
 *   Umami PostgreSQL: website_event (event_name='a11y-action') + event_data (JSON)
 */
(function () {
  'use strict';

  // ========================================
  // A11y 语义提取（从研究方案移植）
  // ========================================

  function captureA11yContext(node) {
    if (!node || node.nodeType !== 1) return null;
    return {
      role: node.getAttribute('role') || inferRole(node),
      name: extractName(node),
      states: extractStates(node),
      actionable: isActionable(node),
      context: extractParentContext(node),
    };
  }

  function inferRole(el) {
    var tag = el.tagName.toLowerCase();
    var roleMap = {
      button: 'button', a: 'link',
      input: inferInputRole(el), select: 'listbox',
      option: 'option', textarea: 'textbox',
      h1: 'heading', h2: 'heading', h3: 'heading',
      ul: 'list', ol: 'list', li: 'listitem',
      nav: 'navigation', main: 'main', header: 'banner',
      footer: 'contentinfo', form: 'form', table: 'table',
      img: 'img', dialog: 'dialog', summary: 'summary',
      details: 'group',
    };
    return roleMap[tag] || 'generic';
  }

  function inferInputRole(el) {
    var type = (el.type || 'text').toLowerCase();
    var typeMap = {
      text: 'textbox', email: 'textbox', tel: 'textbox',
      password: 'textbox', search: 'textbox', url: 'textbox',
      number: 'spinbutton', checkbox: 'checkbox', radio: 'radio',
      range: 'slider', color: 'textbox', date: 'textbox',
      'datetime-local': 'textbox', time: 'textbox', month: 'textbox',
      week: 'textbox', file: 'textbox', submit: 'button',
      button: 'button', reset: 'button', image: 'button',
      hidden: 'textbox',
    };
    return typeMap[type] || 'textbox';
  }

  function extractName(el) {
    var ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim().slice(0, 100);

    var labelledby = el.getAttribute('aria-labelledby');
    if (labelledby) {
      var labelEl = document.getElementById(labelledby);
      if (labelEl) {
        var text = labelEl.textContent.trim();
        if (text) return text.slice(0, 100);
      }
    }

    if (el.id) {
      var labelFor = document.querySelector('label[for="' + el.id + '"]');
      if (labelFor) {
        var text = labelFor.textContent.trim();
        if (text) return text.slice(0, 100);
      }
    }

    // 3.5. Parent label (nested: <label><input type="checkbox">Text</label>)
    var parentLabel = el.closest('label');
    if (parentLabel && parentLabel !== el) {
      var labelText = parentLabel.textContent.trim();
      if (labelText) return labelText.slice(0, 100);
    }

    var role = el.getAttribute('role') || inferRole(el);
    if (['button', 'link', 'heading', 'option', 'listitem', 'summary', 'tab', 'menuitem'].indexOf(role) !== -1) {
      var text = el.textContent.trim();
      if (text) return text.slice(0, 100);
    }

    var placeholder = el.getAttribute('placeholder');
    if (placeholder) return placeholder.slice(0, 100);

    var alt = el.getAttribute('alt');
    if (alt) return alt.slice(0, 100);

    var title = el.getAttribute('title');
    if (title) return title.slice(0, 100);

    return null;
  }

  function extractStates(el) {
    var states = {};
    var attrs = ['aria-checked', 'aria-expanded', 'aria-selected',
                 'aria-pressed', 'aria-disabled', 'aria-hidden'];
    for (var i = 0; i < attrs.length; i++) {
      var val = el.getAttribute(attrs[i]);
      if (val !== null) states[attrs[i].replace('aria-', '')] = val;
    }
    if (el.disabled) states.disabled = true;
    if (el.matches(':focus')) states.focused = true;
    if (el.hasAttribute('hidden')) states.hidden = true;
    if (el.checked) states.checked = 'true';
    return states;
  }

  function isActionable(el) {
    return el.matches(
      'a, button, input, select, textarea, [role="button"], [role="link"], ' +
      '[role="textbox"], [role="checkbox"], [role="tab"], [role="option"], ' +
      '[role="menuitem"], [tabindex]:not([tabindex="-1"])'
    );
  }

  function extractParentContext(el) {
    var semantic = el.closest(
      '[role="navigation"], [role="main"], [role="dialog"], [role="tabpanel"], ' +
      '[role="tablist"], [role="form"], nav, main, aside, section, article, form, fieldset'
    );
    return semantic ? {
      role: semantic.getAttribute('role') || semantic.tagName.toLowerCase(),
      label: semantic.getAttribute('aria-label')
        || (function() {
            var h = semantic.querySelector('h1,h2,h3');
            return h ? h.textContent.trim().slice(0, 50) : null;
        })(),
    } : null;
  }

  // ========================================
  // 隐私脱敏
  // ========================================

  var SENSITIVE_SELECTORS = [
    'input[type="password"]',
    'input[name*="credit"]', 'input[name*="card"]',
    'input[name*="ssn"]', 'input[name*="id-number"]',
  ];
  var PII_SELECTORS = {
    'input[type="email"]': '{email}',
    'input[type="tel"]': '{phone}',
    'input[name*="name"]': '{name}',
    'input[name*="address"]': '{address}',
  };

  function sanitizeValue(el, value) {
    if (!value) return value;
    try {
      if (el.matches(SENSITIVE_SELECTORS.join(','))) return '[REDACTED]';
      var keys = Object.keys(PII_SELECTORS);
      for (var i = 0; i < keys.length; i++) {
        if (el.matches(keys[i])) return PII_SELECTORS[keys[i]];
      }
    } catch (e) {}
    return value;
  }

  // ========================================
  // Session IDs — 双层 session
  // 1. sessionId: Umami 浏览器 session（跨页面，30分钟超时）
  // 2. pageSessionId: 页面 session（每次刷新/加载生成新 UUID）
  // ========================================

  var _sessionId = null;
  var PAGE_SESSION_ID = (window.crypto && crypto.randomUUID)
    ? crypto.randomUUID()
    : 'page-' + Date.now() + '-' + Math.random().toString(36).slice(2);

  function getSessionId() {
    if (_sessionId) return _sessionId;
    try {
      if (typeof umami !== 'undefined' && umami.getSession) {
        var session = umami.getSession();
        if (session && session.cache) {
          var parts = session.cache.split('.');
          if (parts.length >= 2) {
            var payload = JSON.parse(atob(parts[1]));
            if (payload.sessionId) {
              _sessionId = payload.sessionId;
              return _sessionId;
            }
          }
        }
      }
    } catch (e) {}
    return 'pending-' + Date.now();
  }

  var actionCount = 0;
  var inputBuffer = {};
  // Clean up expired debounce entries every 30s to prevent unbounded growth
  setInterval(function() {
    var now = Date.now();
    Object.keys(inputBuffer).forEach(function(key) {
      if (now - inputBuffer[key] > 5000) delete inputBuffer[key];
    });
  }, 30000);

  function trackA11yAction(eventType, element, extra) {
    var a11y = captureA11yContext(element);
    if (!a11y) return;

    // 构建 TOON 格式的紧凑表示
    var states = a11y.states && Object.keys(a11y.states).length > 0
      ? '{' + Object.keys(a11y.states).map(function(k) { return k + ':' + a11y.states[k]; }).join(',') + '}'
      : '';
    var ctx = a11y.context
      ? a11y.context.role + (a11y.context.label ? '("' + a11y.context.label + '")' : '')
      : '';

    // select 选中项或 input 值追加到 TOON
    var valueInfo = '';
    if (extra && extra.selectedText) {
      valueInfo = ' v:"' + extra.selectedText + '"';
    } else if (extra && extra.inputValue !== undefined && extra.inputValue !== null) {
      valueInfo = ' v:"' + extra.inputValue + '"';
    }

    var toonLine = [
      eventType,
      'r:' + a11y.role,
      a11y.name ? 'n:"' + a11y.name + '"' : '',
      states ? 's:' + states : '',
      ctx ? 'ctx:' + ctx : '',
      valueInfo,
    ].filter(Boolean).join(' ');

    var payload = {
      eventType: eventType,
      role: a11y.role,
      name: a11y.name,
      states: a11y.states,
      actionable: a11y.actionable,
      context: a11y.context,
      toon: toonLine,
      sessionId: getSessionId(),
      pageSessionId: PAGE_SESSION_ID,
      timestamp: Date.now(),
    };

    // 附加额外数据
    if (extra) {
      if (extra.selectedValue !== undefined) payload.selectedValue = extra.selectedValue;
      if (extra.selectedText !== undefined) payload.selectedText = extra.selectedText;
      if (extra.inputValue !== undefined) payload.inputValue = extra.inputValue;
    }

    // 通过 Umami 自定义事件发送
    if (typeof umami !== 'undefined' && umami.track) {
      umami.track('a11y-action', payload);
    }

    actionCount++;
    updateStatusUI(toonLine, actionCount);

    if (window.console) console.log('[A11y] ' + toonLine);
  }

  function updateStatusUI(toonLine, count) {
    var el = document.getElementById('a11y-count');
    if (el) el.textContent = 'A11y Actions: ' + count;
  }

  // ========================================
  // 事件监听
  // ========================================

  document.addEventListener('click', function (e) {
    var el = e.target.closest('a, button, input, select, textarea, [role="button"], [role="tab"], [role="link"], [role="checkbox"], [role="option"]');
    if (!el) el = e.target;
    if (el && el.nodeType === 1) {
      trackA11yAction('click', el);
    }
  }, true);

  // input 事件防抖（500ms 内同一元素只发一次）
  document.addEventListener('input', function (e) {
    var el = e.target;
    if (!el || el.nodeType !== 1) return;

    var key = el.id || el.name || el.tagName;
    var now = Date.now();
    if (inputBuffer[key] && now - inputBuffer[key] < 500) return;
    inputBuffer[key] = now;

    // 脱敏输入值后传入
    var sanitized = sanitizeValue(el, el.value);
    trackA11yAction('input', el, { inputValue: sanitized });
  }, true);

  document.addEventListener('change', function (e) {
    var el = e.target;
    if (!el || el.nodeType !== 1) return;

    // select 元素：捕获选中的 option 文本和值
    if (el.tagName === 'SELECT' && el.options.length > 0) {
      var opt = el.options[el.selectedIndex];
      trackA11yAction('change', el, {
        selectedValue: opt.value,
        selectedText: opt.text,
      });
    } else {
      trackA11yAction('change', el);
    }
  }, true);

  // 暴露 API 供外部使用
  window.A11yEnhancer = {
    captureA11yContext: captureA11yContext,
    sanitizeValue: sanitizeValue,
    getSessionId: function() { return getSessionId(); },
    getPageSessionId: function() { return PAGE_SESSION_ID; },
    getActionCount: function() { return actionCount; },
  };

  console.log('[A11y] Enhancer initialized. PageSession: ' + PAGE_SESSION_ID.slice(0, 8));
})();
