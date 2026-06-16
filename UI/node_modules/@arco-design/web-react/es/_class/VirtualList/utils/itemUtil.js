var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
import { findDOMNode } from '../../../_util/react-dom';
import getStringLength from '../../../_util/getStringLength';
/**
 * 为了计算方便，定位元素的下标可能返回数组长度，代表最后一个元素
 */
export var GHOST_ITEM_KEY = '__rc_ghost_item__';
/**
 * 根据滚动条当前的滚动百分比，计算出基准元素
 * 在基准元素的上方和下方渲染可见区域的其他元素
 */
export function getLocationItem(scrollPtg, total) {
    var itemIndex = Math.floor(scrollPtg * total);
    var itemTopPtg = itemIndex / total;
    var offsetPtg = (scrollPtg - itemTopPtg) / (1 / total);
    return {
        index: itemIndex,
        // scrollPtg >= itemTopPtg，计算结果为元素应当补充的滚动距离相对自身高度的偏移量
        offsetPtg: Number.isNaN(offsetPtg) ? 0 : offsetPtg,
    };
}
/**
 * 获取HTML元素高度
 */
export function getNodeHeight(node, needMargin) {
    if (needMargin === void 0) { needMargin = false; }
    var element = findDOMNode(node);
    var marginVertical = 0;
    if (needMargin) {
        var _a = window.getComputedStyle(node), marginTop = _a.marginTop, marginBottom = _a.marginBottom;
        marginVertical = Number(marginTop.replace(/\D/g, '')) + Number(marginBottom.replace(/\D/g, ''));
        marginVertical = isNaN(marginVertical) ? 0 : marginVertical;
    }
    return element ? element.offsetHeight + marginVertical : 0;
}
/**
 * 获取有效的scrollTop值
 * Safari的缓动效果会获得负值的scrollTop
 */
export function getValidScrollTop(scrollTop, scrollRange) {
    return scrollTop < 0 ? 0 : scrollTop > scrollRange ? scrollRange : scrollTop;
}
/**
 * 视口已滚动距离 / 总可滚动距离
 */
export function getScrollPercentage(_a) {
    var scrollTop = _a.scrollTop, scrollHeight = _a.scrollHeight, clientHeight = _a.clientHeight;
    var scrollRange = scrollHeight - clientHeight;
    return scrollRange <= 0 ? 0 : getValidScrollTop(scrollTop, scrollRange) / scrollRange;
}
/**
 * 计算需要渲染的元素的开始下标、结束下标和用于定位的元素下标
 */
export function getRangeIndex(scrollPtg, itemCount, visibleCount) {
    var _a = getLocationItem(scrollPtg, itemCount), index = _a.index, offsetPtg = _a.offsetPtg;
    var beforeCount = Math.ceil(scrollPtg * visibleCount);
    var afterCount = Math.ceil((1 - scrollPtg) * visibleCount);
    return {
        itemIndex: index,
        itemOffsetPtg: offsetPtg,
        startIndex: Math.max(0, index - beforeCount),
        endIndex: Math.min(itemCount - 1, index + afterCount),
    };
}
/**
 * 计算元素相对于视口顶部的偏移量
 */
export function getItemRelativeTop(_a) {
    var itemHeight = _a.itemHeight, itemOffsetPtg = _a.itemOffsetPtg, scrollPtg = _a.scrollPtg, clientHeight = _a.clientHeight;
    return Math.floor(clientHeight * scrollPtg - itemHeight * itemOffsetPtg);
}
/**
 * 计算元素相对于整个滚动区域顶部的偏移量
 */
export function getItemAbsoluteTop(_a) {
    var scrollTop = _a.scrollTop, rest = __rest(_a, ["scrollTop"]);
    return scrollTop + getItemRelativeTop(rest);
}
/**
 * 计算某一指定下标的元素相对于视口顶部的偏移量
 */
export function getCompareItemRelativeTop(_a) {
    var locatedItemRelativeTop = _a.locatedItemRelativeTop, locatedItemIndex = _a.locatedItemIndex, compareItemIndex = _a.compareItemIndex, startIndex = _a.startIndex, endIndex = _a.endIndex, getItemKey = _a.getItemKey, itemElementHeights = _a.itemElementHeights, itemHeight = _a.itemHeight;
    var compareItemTop = locatedItemRelativeTop;
    var compareItemKey = getItemKey(compareItemIndex);
    if (compareItemIndex <= locatedItemIndex) {
        for (var index = locatedItemIndex; index >= startIndex; index -= 1) {
            var key = getItemKey(index);
            if (key === compareItemKey) {
                break;
            }
            var prevItemKey = getItemKey(index - 1);
            compareItemTop -= itemElementHeights[prevItemKey] || itemHeight;
        }
    }
    else {
        for (var index = locatedItemIndex; index <= endIndex; index += 1) {
            var key = getItemKey(index);
            if (key === compareItemKey) {
                break;
            }
            compareItemTop += itemElementHeights[key] || itemHeight;
        }
    }
    return compareItemTop;
}
function getTextLengthFromNode(node) {
    var _a, _b, _c, _d;
    // 处理 null / undefined
    if (node === null || node === undefined) {
        return 0;
    }
    // 处理字符串
    if (typeof node === 'string') {
        return getStringLength(node);
    }
    // 处理数字
    if (typeof node === 'number') {
        return getStringLength(String(node));
    }
    // 处理数组，递归计算
    if (Array.isArray(node)) {
        return node.reduce(function (acc, child) { return acc + getTextLengthFromNode(child); }, 0);
    }
    // 处理 ReactElement，优先递归获取 children，兼容文本直接挂在 props 上的场景
    if (typeof node === 'object' && node !== null && 'props' in node) {
        var reactElement = node;
        if (((_a = reactElement.props) === null || _a === void 0 ? void 0 : _a.children) !== undefined) {
            return getTextLengthFromNode(reactElement.props.children);
        }
        if (((_b = reactElement.props) === null || _b === void 0 ? void 0 : _b.text) !== undefined) {
            return getTextLengthFromNode(reactElement.props.text);
        }
        if (((_c = reactElement.props) === null || _c === void 0 ? void 0 : _c.label) !== undefined) {
            return getTextLengthFromNode(reactElement.props.label);
        }
        if (((_d = reactElement.props) === null || _d === void 0 ? void 0 : _d.title) !== undefined) {
            return getTextLengthFromNode(reactElement.props.title);
        }
    }
    return 0;
}
export function getLongestItemIndex(data) {
    var result = -1;
    var maxLength = 0;
    data.forEach(function (item, index) {
        var _a;
        var node = typeof item === 'string' ? item : (_a = item.props) === null || _a === void 0 ? void 0 : _a.children;
        var length = getTextLengthFromNode(node);
        if (length > maxLength) {
            maxLength = length;
            result = index;
        }
    });
    return result;
}
