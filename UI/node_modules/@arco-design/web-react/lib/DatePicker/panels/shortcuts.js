"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var react_1 = __importStar(require("react"));
var Button_1 = __importDefault(require("../../Button"));
var is_1 = require("../../_util/is");
var util_1 = require("../util");
function Shortcuts(props, ref) {
    var prefixCls = props.prefixCls, _a = props.shortcuts, shortcuts = _a === void 0 ? [] : _a, onSelectNow = props.onSelectNow, nowText = props.nowText, showNowBtn = props.showNowBtn, showTime = props.showTime, onMouseEnterShortcut = props.onMouseEnterShortcut, onMouseLeaveShortcut = props.onMouseLeaveShortcut, nowDisabled = props.nowDisabled, disabledDate = props.disabledDate, _b = props.mode, mode = _b === void 0 ? 'date' : _b;
    function onMouseEnter(shortcut) {
        onMouseEnterShortcut && onMouseEnterShortcut(shortcut);
    }
    function onMouseLeave(shortcut) {
        onMouseLeaveShortcut && onMouseLeaveShortcut(shortcut);
    }
    function onClick(shortcut, e) {
        var onSelectShortcut = props.onSelectShortcut;
        if (getShortcutDisabled(shortcut)) {
            return;
        }
        onSelectShortcut && onSelectShortcut(shortcut, e);
    }
    function getShortcutDisabled(shortcut) {
        var shortcutValue = typeof shortcut.value === 'function' && shortcut.value();
        if ((0, is_1.isDayjs)(shortcutValue)) {
            return (0, util_1.isDisabledDate)(shortcutValue, disabledDate, mode);
        }
        if ((0, is_1.isArray)(shortcutValue)) {
            return shortcutValue.some(function (item) { return (0, is_1.isDayjs)(item) && (0, util_1.isDisabledDate)(item, disabledDate, mode); });
        }
        return false;
    }
    var hasShortcuts = (0, is_1.isArray)(shortcuts) && shortcuts.length > 0;
    var shouldShowNowBtn = showNowBtn && showTime && !hasShortcuts;
    return (react_1.default.createElement("div", { ref: ref, className: prefixCls + "-shortcuts" },
        shouldShowNowBtn && (react_1.default.createElement(Button_1.default, { size: "mini", disabled: nowDisabled, onClick: onSelectNow }, nowText)),
        hasShortcuts &&
            shortcuts.map(function (shortcut, index) {
                var disabled = getShortcutDisabled(shortcut);
                return (react_1.default.createElement(Button_1.default, { key: index, size: "mini", disabled: disabled, onMouseEnter: function () { return onMouseEnter(shortcut); }, onMouseLeave: function () { return onMouseLeave(shortcut); }, onClick: function (e) { return onClick(shortcut, e); } }, shortcut.text));
            })));
}
exports.default = (0, react_1.forwardRef)(Shortcuts);
