import React, { forwardRef } from 'react';
import Button from '../../Button';
import { isArray, isDayjs } from '../../_util/is';
import { isDisabledDate } from '../util';
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
        if (isDayjs(shortcutValue)) {
            return isDisabledDate(shortcutValue, disabledDate, mode);
        }
        if (isArray(shortcutValue)) {
            return shortcutValue.some(function (item) { return isDayjs(item) && isDisabledDate(item, disabledDate, mode); });
        }
        return false;
    }
    var hasShortcuts = isArray(shortcuts) && shortcuts.length > 0;
    var shouldShowNowBtn = showNowBtn && showTime && !hasShortcuts;
    return (React.createElement("div", { ref: ref, className: prefixCls + "-shortcuts" },
        shouldShowNowBtn && (React.createElement(Button, { size: "mini", disabled: nowDisabled, onClick: onSelectNow }, nowText)),
        hasShortcuts &&
            shortcuts.map(function (shortcut, index) {
                var disabled = getShortcutDisabled(shortcut);
                return (React.createElement(Button, { key: index, size: "mini", disabled: disabled, onMouseEnter: function () { return onMouseEnter(shortcut); }, onMouseLeave: function () { return onMouseLeave(shortcut); }, onClick: function (e) { return onClick(shortcut, e); } }, shortcut.text));
            })));
}
export default forwardRef(Shortcuts);
