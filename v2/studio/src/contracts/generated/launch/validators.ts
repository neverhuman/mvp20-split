// @ts-nocheck
// Generated standalone validators; change published schemas or the generator, never this file.
var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) => function __require() {
  try {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  } catch (e) {
    throw mod = 0, e;
  }
};

// node_modules/ajv/dist/runtime/ucs2length.js
var require_ucs2length = __commonJS({
  "node_modules/ajv/dist/runtime/ucs2length.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    function ucs2length(str) {
      const len = str.length;
      let length = 0;
      let pos = 0;
      let value;
      while (pos < len) {
        length++;
        value = str.charCodeAt(pos++);
        if (value >= 55296 && value <= 56319 && pos < len) {
          value = str.charCodeAt(pos);
          if ((value & 64512) === 56320)
            pos++;
        }
      }
      return length;
    }
    exports.default = ucs2length;
    ucs2length.code = 'require("ajv/dist/runtime/ucs2length").default';
  }
});

// node_modules/ajv-formats/dist/formats.js
var require_formats = __commonJS({
  "node_modules/ajv-formats/dist/formats.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.formatNames = exports.fastFormats = exports.fullFormats = void 0;
    function fmtDef(validate, compare) {
      return { validate, compare };
    }
    exports.fullFormats = {
      // date: http://tools.ietf.org/html/rfc3339#section-5.6
      date: fmtDef(date, compareDate),
      // date-time: http://tools.ietf.org/html/rfc3339#section-5.6
      time: fmtDef(getTime(true), compareTime),
      "date-time": fmtDef(getDateTime(true), compareDateTime),
      "iso-time": fmtDef(getTime(), compareIsoTime),
      "iso-date-time": fmtDef(getDateTime(), compareIsoDateTime),
      // duration: https://tools.ietf.org/html/rfc3339#appendix-A
      duration: /^P(?!$)((\d+Y)?(\d+M)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?|(\d+W)?)$/,
      uri,
      "uri-reference": /^(?:[a-z][a-z0-9+\-.]*:)?(?:\/?\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:]|%[0-9a-f]{2})*@)?(?:\[(?:(?:(?:(?:[0-9a-f]{1,4}:){6}|::(?:[0-9a-f]{1,4}:){5}|(?:[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){4}|(?:(?:[0-9a-f]{1,4}:){0,1}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){3}|(?:(?:[0-9a-f]{1,4}:){0,2}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){2}|(?:(?:[0-9a-f]{1,4}:){0,3}[0-9a-f]{1,4})?::[0-9a-f]{1,4}:|(?:(?:[0-9a-f]{1,4}:){0,4}[0-9a-f]{1,4})?::)(?:[0-9a-f]{1,4}:[0-9a-f]{1,4}|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?:(?:[0-9a-f]{1,4}:){0,5}[0-9a-f]{1,4})?::[0-9a-f]{1,4}|(?:(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{1,4})?::)|[Vv][0-9a-f]+\.[a-z0-9\-._~!$&'()*+,;=:]+)\]|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)|(?:[a-z0-9\-._~!$&'"()*+,;=]|%[0-9a-f]{2})*)(?::\d*)?(?:\/(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})*)*|\/(?:(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})*)*)?|(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})*)*)?(?:\?(?:[a-z0-9\-._~!$&'"()*+,;=:@/?]|%[0-9a-f]{2})*)?(?:#(?:[a-z0-9\-._~!$&'"()*+,;=:@/?]|%[0-9a-f]{2})*)?$/i,
      // uri-template: https://tools.ietf.org/html/rfc6570
      "uri-template": /^(?:(?:[^\x00-\x20"'<>%\\^`{|}]|%[0-9a-f]{2})|\{[+#./;?&=,!@|]?(?:[a-z0-9_]|%[0-9a-f]{2})+(?::[1-9][0-9]{0,3}|\*)?(?:,(?:[a-z0-9_]|%[0-9a-f]{2})+(?::[1-9][0-9]{0,3}|\*)?)*\})*$/i,
      // For the source: https://gist.github.com/dperini/729294
      // For test cases: https://mathiasbynens.be/demo/url-regex
      url: /^(?:https?|ftp):\/\/(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z0-9\u{00a1}-\u{ffff}]+-)*[a-z0-9\u{00a1}-\u{ffff}]+)(?:\.(?:[a-z0-9\u{00a1}-\u{ffff}]+-)*[a-z0-9\u{00a1}-\u{ffff}]+)*(?:\.(?:[a-z\u{00a1}-\u{ffff}]{2,})))(?::\d{2,5})?(?:\/[^\s]*)?$/iu,
      email: /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i,
      hostname: /^(?=.{1,253}\.?$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[-0-9a-z]{0,61}[0-9a-z])?)*\.?$/i,
      // optimized https://www.safaribooksonline.com/library/view/regular-expressions-cookbook/9780596802837/ch07s16.html
      ipv4: /^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$/,
      ipv6: /^((([0-9a-f]{1,4}:){7}([0-9a-f]{1,4}|:))|(([0-9a-f]{1,4}:){6}(:[0-9a-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9a-f]{1,4}:){5}(((:[0-9a-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9a-f]{1,4}:){4}(((:[0-9a-f]{1,4}){1,3})|((:[0-9a-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9a-f]{1,4}:){3}(((:[0-9a-f]{1,4}){1,4})|((:[0-9a-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9a-f]{1,4}:){2}(((:[0-9a-f]{1,4}){1,5})|((:[0-9a-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9a-f]{1,4}:){1}(((:[0-9a-f]{1,4}){1,6})|((:[0-9a-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9a-f]{1,4}){1,7})|((:[0-9a-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))$/i,
      regex,
      // uuid: http://tools.ietf.org/html/rfc4122
      uuid: /^(?:urn:uuid:)?[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i,
      // JSON-pointer: https://tools.ietf.org/html/rfc6901
      // uri fragment: https://tools.ietf.org/html/rfc3986#appendix-A
      "json-pointer": /^(?:\/(?:[^~/]|~0|~1)*)*$/,
      "json-pointer-uri-fragment": /^#(?:\/(?:[a-z0-9_\-.!$&'()*+,;:=@]|%[0-9a-f]{2}|~0|~1)*)*$/i,
      // relative JSON-pointer: http://tools.ietf.org/html/draft-luff-relative-json-pointer-00
      "relative-json-pointer": /^(?:0|[1-9][0-9]*)(?:#|(?:\/(?:[^~/]|~0|~1)*)*)$/,
      // the following formats are used by the openapi specification: https://spec.openapis.org/oas/v3.0.0#data-types
      // byte: https://github.com/miguelmota/is-base64
      byte,
      // signed 32 bit integer
      int32: { type: "number", validate: validateInt32 },
      // signed 64 bit integer
      int64: { type: "number", validate: validateInt64 },
      // C-type float
      float: { type: "number", validate: validateNumber },
      // C-type double
      double: { type: "number", validate: validateNumber },
      // hint to the UI to hide input strings
      password: true,
      // unchecked string payload
      binary: true
    };
    exports.fastFormats = {
      ...exports.fullFormats,
      date: fmtDef(/^\d\d\d\d-[0-1]\d-[0-3]\d$/, compareDate),
      time: fmtDef(/^(?:[0-2]\d:[0-5]\d:[0-5]\d|23:59:60)(?:\.\d+)?(?:z|[+-]\d\d(?::?\d\d)?)$/i, compareTime),
      "date-time": fmtDef(/^\d\d\d\d-[0-1]\d-[0-3]\dt(?:[0-2]\d:[0-5]\d:[0-5]\d|23:59:60)(?:\.\d+)?(?:z|[+-]\d\d(?::?\d\d)?)$/i, compareDateTime),
      "iso-time": fmtDef(/^(?:[0-2]\d:[0-5]\d:[0-5]\d|23:59:60)(?:\.\d+)?(?:z|[+-]\d\d(?::?\d\d)?)?$/i, compareIsoTime),
      "iso-date-time": fmtDef(/^\d\d\d\d-[0-1]\d-[0-3]\d[t\s](?:[0-2]\d:[0-5]\d:[0-5]\d|23:59:60)(?:\.\d+)?(?:z|[+-]\d\d(?::?\d\d)?)?$/i, compareIsoDateTime),
      // uri: https://github.com/mafintosh/is-my-json-valid/blob/master/formats.js
      uri: /^(?:[a-z][a-z0-9+\-.]*:)(?:\/?\/)?[^\s]*$/i,
      "uri-reference": /^(?:(?:[a-z][a-z0-9+\-.]*:)?\/?\/)?(?:[^\\\s#][^\s#]*)?(?:#[^\\\s]*)?$/i,
      // email (sources from jsen validator):
      // http://stackoverflow.com/questions/201323/using-a-regular-expression-to-validate-an-email-address#answer-8829363
      // http://www.w3.org/TR/html5/forms.html#valid-e-mail-address (search for 'wilful violation')
      email: /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$/i
    };
    exports.formatNames = Object.keys(exports.fullFormats);
    function isLeapYear(year) {
      return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    }
    var DATE = /^(\d\d\d\d)-(\d\d)-(\d\d)$/;
    var DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    function date(str) {
      const matches = DATE.exec(str);
      if (!matches)
        return false;
      const year = +matches[1];
      const month = +matches[2];
      const day = +matches[3];
      return month >= 1 && month <= 12 && day >= 1 && day <= (month === 2 && isLeapYear(year) ? 29 : DAYS[month]);
    }
    function compareDate(d1, d2) {
      if (!(d1 && d2))
        return void 0;
      if (d1 > d2)
        return 1;
      if (d1 < d2)
        return -1;
      return 0;
    }
    var TIME = /^(\d\d):(\d\d):(\d\d(?:\.\d+)?)(z|([+-])(\d\d)(?::?(\d\d))?)?$/i;
    function getTime(strictTimeZone) {
      return function time(str) {
        const matches = TIME.exec(str);
        if (!matches)
          return false;
        const hr = +matches[1];
        const min = +matches[2];
        const sec = +matches[3];
        const tz = matches[4];
        const tzSign = matches[5] === "-" ? -1 : 1;
        const tzH = +(matches[6] || 0);
        const tzM = +(matches[7] || 0);
        if (tzH > 23 || tzM > 59 || strictTimeZone && !tz)
          return false;
        if (hr <= 23 && min <= 59 && sec < 60)
          return true;
        const utcMin = min - tzM * tzSign;
        const utcHr = hr - tzH * tzSign - (utcMin < 0 ? 1 : 0);
        return (utcHr === 23 || utcHr === -1) && (utcMin === 59 || utcMin === -1) && sec < 61;
      };
    }
    function compareTime(s1, s2) {
      if (!(s1 && s2))
        return void 0;
      const t1 = (/* @__PURE__ */ new Date("2020-01-01T" + s1)).valueOf();
      const t2 = (/* @__PURE__ */ new Date("2020-01-01T" + s2)).valueOf();
      if (!(t1 && t2))
        return void 0;
      return t1 - t2;
    }
    function compareIsoTime(t1, t2) {
      if (!(t1 && t2))
        return void 0;
      const a1 = TIME.exec(t1);
      const a2 = TIME.exec(t2);
      if (!(a1 && a2))
        return void 0;
      t1 = a1[1] + a1[2] + a1[3];
      t2 = a2[1] + a2[2] + a2[3];
      if (t1 > t2)
        return 1;
      if (t1 < t2)
        return -1;
      return 0;
    }
    var DATE_TIME_SEPARATOR = /t|\s/i;
    function getDateTime(strictTimeZone) {
      const time = getTime(strictTimeZone);
      return function date_time(str) {
        const dateTime = str.split(DATE_TIME_SEPARATOR);
        return dateTime.length === 2 && date(dateTime[0]) && time(dateTime[1]);
      };
    }
    function compareDateTime(dt1, dt2) {
      if (!(dt1 && dt2))
        return void 0;
      const d1 = new Date(dt1).valueOf();
      const d2 = new Date(dt2).valueOf();
      if (!(d1 && d2))
        return void 0;
      return d1 - d2;
    }
    function compareIsoDateTime(dt1, dt2) {
      if (!(dt1 && dt2))
        return void 0;
      const [d1, t1] = dt1.split(DATE_TIME_SEPARATOR);
      const [d2, t2] = dt2.split(DATE_TIME_SEPARATOR);
      const res = compareDate(d1, d2);
      if (res === void 0)
        return void 0;
      return res || compareTime(t1, t2);
    }
    var NOT_URI_FRAGMENT = /\/|:/;
    var URI = /^(?:[a-z][a-z0-9+\-.]*:)(?:\/?\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:]|%[0-9a-f]{2})*@)?(?:\[(?:(?:(?:(?:[0-9a-f]{1,4}:){6}|::(?:[0-9a-f]{1,4}:){5}|(?:[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){4}|(?:(?:[0-9a-f]{1,4}:){0,1}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){3}|(?:(?:[0-9a-f]{1,4}:){0,2}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){2}|(?:(?:[0-9a-f]{1,4}:){0,3}[0-9a-f]{1,4})?::[0-9a-f]{1,4}:|(?:(?:[0-9a-f]{1,4}:){0,4}[0-9a-f]{1,4})?::)(?:[0-9a-f]{1,4}:[0-9a-f]{1,4}|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?:(?:[0-9a-f]{1,4}:){0,5}[0-9a-f]{1,4})?::[0-9a-f]{1,4}|(?:(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{1,4})?::)|[Vv][0-9a-f]+\.[a-z0-9\-._~!$&'()*+,;=:]+)\]|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)|(?:[a-z0-9\-._~!$&'()*+,;=]|%[0-9a-f]{2})*)(?::\d*)?(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*|\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*)?|(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*)(?:\?(?:[a-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9a-f]{2})*)?(?:#(?:[a-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9a-f]{2})*)?$/i;
    function uri(str) {
      return NOT_URI_FRAGMENT.test(str) && URI.test(str);
    }
    var BYTE = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/gm;
    function byte(str) {
      BYTE.lastIndex = 0;
      return BYTE.test(str);
    }
    var MIN_INT32 = -(2 ** 31);
    var MAX_INT32 = 2 ** 31 - 1;
    function validateInt32(value) {
      return Number.isInteger(value) && value <= MAX_INT32 && value >= MIN_INT32;
    }
    function validateInt64(value) {
      return Number.isInteger(value);
    }
    function validateNumber() {
      return true;
    }
    var Z_ANCHOR = /[^\\]\\Z/;
    function regex(str) {
      if (Z_ANCHOR.test(str))
        return false;
      try {
        new RegExp(str);
        return true;
      } catch (e) {
        return false;
      }
    }
  }
});

// reviewed-validators.cjs
var require_reviewed_validators = __commonJS({
  "reviewed-validators.cjs"(exports) {
    exports.request = validate20;
    var func1 = require_ucs2length().default;
    var pattern4 = new RegExp("^[A-Za-z0-9][A-Za-z0-9._:-]*$", "u");
    function validate21(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate21.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.command_family === void 0 && (missing0 = "command_family") || data.command_id === void 0 && (missing0 = "command_id") || data.scope === void 0 && (missing0 = "scope") || data.actor_id === void 0 && (missing0 = "actor_id")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "actor_id" || key0 === "command_family" || key0 === "command_id" || key0 === "schema_version" || key0 === "scope")) {
                validate21.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.actor_id !== void 0) {
                let data0 = data.actor_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate21.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate21.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate21.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate21.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.command_family !== void 0) {
                  let data1 = data.command_family;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate21.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate21.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate21.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate21.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.command_id !== void 0) {
                    let data2 = data.command_id;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          validate21.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate21.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern4.test(data2)) {
                              validate21.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate21.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.schema_version !== void 0) {
                      let data3 = data.schema_version;
                      const _errs8 = errors;
                      if (typeof data3 !== "string") {
                        validate21.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data3) {
                        validate21.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope !== void 0) {
                        let data4 = data.scope;
                        const _errs10 = errors;
                        const _errs11 = errors;
                        if (errors === _errs11) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.tenant_id === void 0 && (missing1 = "tenant_id") || data4.project_id === void 0 && (missing1 = "project_id")) {
                              validate21.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate21.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs13 === errors) {
                                if (data4.project_id !== void 0) {
                                  let data5 = data4.project_id;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 128) {
                                        validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
                                            validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data4.tenant_id !== void 0) {
                                    let data6 = data4.tenant_id;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 === "string") {
                                        if (func1(data6) > 128) {
                                          validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
                                              validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid2 = _errs16 === errors;
                                  } else {
                                    var valid2 = true;
                                  }
                                }
                              }
                            }
                          } else {
                            validate21.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs10 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate21.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate21.errors = vErrors;
      return errors === 0;
    }
    validate21.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern9 = new RegExp("^[0-9a-f]{64}$", "u");
    var pattern14 = new RegExp("^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$", "u");
    var pattern16 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
    function validate29(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate29.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate29.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate29.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact_id !== void 0) {
                let data0 = data.artifact_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate29.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate29.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate29.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate29.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.media_type !== void 0) {
                  let data1 = data.media_type;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate29.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate29.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern16.test(data1)) {
                            validate29.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate29.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.schema_ref !== void 0) {
                    let data2 = data.schema_ref;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.schema_id === void 0 && (missing1 = "schema_id") || data2.version === void 0 && (missing1 = "version") || data2.sha256 === void 0 && (missing1 = "sha256")) {
                          validate29.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate29.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.schema_id !== void 0) {
                              let data3 = data2.schema_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate29.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate29.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate29.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate29.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.sha256 !== void 0) {
                                let data4 = data2.sha256;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (!pattern9.test(data4)) {
                                      validate29.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate29.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data2.version !== void 0) {
                                  let data5 = data2.version;
                                  const _errs14 = errors;
                                  if (typeof data5 !== "string") {
                                    validate29.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate29.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate29.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scope !== void 0) {
                      let data6 = data.scope;
                      const _errs16 = errors;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                          let missing2;
                          if (data6.tenant_id === void 0 && (missing2 = "tenant_id") || data6.project_id === void 0 && (missing2 = "project_id")) {
                            validate29.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate29.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs19 === errors) {
                              if (data6.project_id !== void 0) {
                                let data7 = data6.project_id;
                                const _errs20 = errors;
                                if (errors === _errs20) {
                                  if (typeof data7 === "string") {
                                    if (func1(data7) > 128) {
                                      validate29.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate29.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate29.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate29.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid4 = _errs20 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data6.tenant_id !== void 0) {
                                  let data8 = data6.tenant_id;
                                  const _errs22 = errors;
                                  if (errors === _errs22) {
                                    if (typeof data8 === "string") {
                                      if (func1(data8) > 128) {
                                        validate29.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate29.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate29.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate29.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate29.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.sha256 !== void 0) {
                        let data9 = data.sha256;
                        const _errs24 = errors;
                        if (errors === _errs24) {
                          if (typeof data9 === "string") {
                            if (!pattern9.test(data9)) {
                              validate29.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate29.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.size_bytes !== void 0) {
                          let data10 = data.size_bytes;
                          const _errs26 = errors;
                          if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                            validate29.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate29.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate29.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                  return false;
                                }
                              }
                            }
                          }
                          var valid0 = _errs26 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate29.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate29.errors = vErrors;
      return errors === 0;
    }
    validate29.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate28(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate28.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.artifact === void 0 && (missing0 = "artifact") || data.representation === void 0 && (missing0 = "representation") || data.unit === void 0 && (missing0 = "unit")) {
            validate28.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "kind" || key0 === "representation" || key0 === "unit")) {
                validate28.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate29(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate29.errors : vErrors.concat(validate29.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.kind !== void 0) {
                  let data1 = data.kind;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate28.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("artifact" !== data1) {
                    validate28.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "artifact" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.representation !== void 0) {
                    let data2 = data.representation;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          validate28.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate28.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern4.test(data2)) {
                              validate28.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate28.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.unit !== void 0) {
                      let data3 = data.unit;
                      const _errs7 = errors;
                      if (errors === _errs7) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 64) {
                            validate28.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate28.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            }
                          }
                        } else {
                          validate28.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        } else {
          validate28.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate28.errors = vErrors;
      return errors === 0;
    }
    validate28.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate32(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate32.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.items === void 0 && (missing0 = "items")) {
            validate32.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "items" || key0 === "kind")) {
                validate32.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.items !== void 0) {
                let data0 = data.items;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 1e4) {
                      validate32.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/maxItems", keyword: "maxItems", params: { limit: 1e4 }, message: "must NOT have more than 10000 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        let data1 = data0[i0];
                        const _errs4 = errors;
                        const _errs5 = errors;
                        let valid2 = false;
                        const _errs6 = errors;
                        const _errs7 = errors;
                        let valid3 = false;
                        let passing0 = null;
                        const _errs8 = errors;
                        const _errs9 = errors;
                        if (errors === _errs9) {
                          if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                            let missing1;
                            if (data1.kind === void 0 && (missing1 = "kind") || data1.value === void 0 && (missing1 = "value")) {
                              const err0 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/BooleanConstant/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              const _errs11 = errors;
                              for (const key1 in data1) {
                                if (!(key1 === "kind" || key1 === "value")) {
                                  const err1 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/BooleanConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err1];
                                  } else {
                                    vErrors.push(err1);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs11 === errors) {
                                if (data1.kind !== void 0) {
                                  let data2 = data1.kind;
                                  const _errs12 = errors;
                                  if (typeof data2 !== "string") {
                                    const err2 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                  }
                                  if ("boolean" !== data2) {
                                    const err3 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/const", keyword: "const", params: { allowedValue: "boolean" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  }
                                  var valid5 = _errs12 === errors;
                                } else {
                                  var valid5 = true;
                                }
                                if (valid5) {
                                  if (data1.value !== void 0) {
                                    const _errs14 = errors;
                                    if (typeof data1.value !== "boolean") {
                                      const err4 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/BooleanConstant/properties/value/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                      if (vErrors === null) {
                                        vErrors = [err4];
                                      } else {
                                        vErrors.push(err4);
                                      }
                                      errors++;
                                    }
                                    var valid5 = _errs14 === errors;
                                  } else {
                                    var valid5 = true;
                                  }
                                }
                              }
                            }
                          } else {
                            const err5 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/BooleanConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err5];
                            } else {
                              vErrors.push(err5);
                            }
                            errors++;
                          }
                        }
                        var _valid1 = _errs8 === errors;
                        if (_valid1) {
                          valid3 = true;
                          passing0 = 0;
                          var props0 = true;
                        }
                        const _errs16 = errors;
                        const _errs17 = errors;
                        if (errors === _errs17) {
                          if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                            let missing2;
                            if (data1.kind === void 0 && (missing2 = "kind") || data1.value === void 0 && (missing2 = "value")) {
                              const err6 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/IntegerConstant/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                              if (vErrors === null) {
                                vErrors = [err6];
                              } else {
                                vErrors.push(err6);
                              }
                              errors++;
                            } else {
                              const _errs19 = errors;
                              for (const key2 in data1) {
                                if (!(key2 === "kind" || key2 === "unit" || key2 === "value")) {
                                  const err7 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/IntegerConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err7];
                                  } else {
                                    vErrors.push(err7);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs19 === errors) {
                                if (data1.kind !== void 0) {
                                  let data4 = data1.kind;
                                  const _errs20 = errors;
                                  if (typeof data4 !== "string") {
                                    const err8 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err8];
                                    } else {
                                      vErrors.push(err8);
                                    }
                                    errors++;
                                  }
                                  if ("integer" !== data4) {
                                    const err9 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/const", keyword: "const", params: { allowedValue: "integer" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err9];
                                    } else {
                                      vErrors.push(err9);
                                    }
                                    errors++;
                                  }
                                  var valid7 = _errs20 === errors;
                                } else {
                                  var valid7 = true;
                                }
                                if (valid7) {
                                  if (data1.unit !== void 0) {
                                    let data5 = data1.unit;
                                    const _errs22 = errors;
                                    if (errors === _errs22) {
                                      if (typeof data5 === "string") {
                                        if (func1(data5) > 64) {
                                          const err10 = { instancePath: instancePath + "/items/" + i0 + "/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err10];
                                          } else {
                                            vErrors.push(err10);
                                          }
                                          errors++;
                                        } else {
                                          if (func1(data5) < 1) {
                                            const err11 = { instancePath: instancePath + "/items/" + i0 + "/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err11];
                                            } else {
                                              vErrors.push(err11);
                                            }
                                            errors++;
                                          }
                                        }
                                      } else {
                                        const err12 = { instancePath: instancePath + "/items/" + i0 + "/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err12];
                                        } else {
                                          vErrors.push(err12);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid7 = _errs22 === errors;
                                  } else {
                                    var valid7 = true;
                                  }
                                  if (valid7) {
                                    if (data1.value !== void 0) {
                                      let data6 = data1.value;
                                      const _errs24 = errors;
                                      if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                        const err13 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/IntegerConstant/properties/value/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                        if (vErrors === null) {
                                          vErrors = [err13];
                                        } else {
                                          vErrors.push(err13);
                                        }
                                        errors++;
                                      }
                                      if (errors === _errs24) {
                                        if (typeof data6 == "number" && isFinite(data6)) {
                                          if (data6 > 9007199254740991 || isNaN(data6)) {
                                            const err14 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/IntegerConstant/properties/value/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" };
                                            if (vErrors === null) {
                                              vErrors = [err14];
                                            } else {
                                              vErrors.push(err14);
                                            }
                                            errors++;
                                          } else {
                                            if (data6 < -9007199254740991 || isNaN(data6)) {
                                              const err15 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/IntegerConstant/properties/value/minimum", keyword: "minimum", params: { comparison: ">=", limit: -9007199254740991 }, message: "must be >= -9007199254740991" };
                                              if (vErrors === null) {
                                                vErrors = [err15];
                                              } else {
                                                vErrors.push(err15);
                                              }
                                              errors++;
                                            }
                                          }
                                        }
                                      }
                                      var valid7 = _errs24 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err16 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/IntegerConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err16];
                            } else {
                              vErrors.push(err16);
                            }
                            errors++;
                          }
                        }
                        var _valid1 = _errs16 === errors;
                        if (_valid1 && valid3) {
                          valid3 = false;
                          passing0 = [passing0, 1];
                        } else {
                          if (_valid1) {
                            valid3 = true;
                            passing0 = 1;
                            if (props0 !== true) {
                              props0 = true;
                            }
                          }
                          const _errs26 = errors;
                          const _errs27 = errors;
                          if (errors === _errs27) {
                            if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                              let missing3;
                              if (data1.kind === void 0 && (missing3 = "kind") || data1.value === void 0 && (missing3 = "value")) {
                                const err17 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/NumberValue/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                                if (vErrors === null) {
                                  vErrors = [err17];
                                } else {
                                  vErrors.push(err17);
                                }
                                errors++;
                              } else {
                                const _errs29 = errors;
                                for (const key3 in data1) {
                                  if (!(key3 === "kind" || key3 === "unit" || key3 === "value")) {
                                    const err18 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/NumberValue/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" };
                                    if (vErrors === null) {
                                      vErrors = [err18];
                                    } else {
                                      vErrors.push(err18);
                                    }
                                    errors++;
                                    break;
                                  }
                                }
                                if (_errs29 === errors) {
                                  if (data1.kind !== void 0) {
                                    let data7 = data1.kind;
                                    const _errs30 = errors;
                                    if (typeof data7 !== "string") {
                                      const err19 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/NumberValue/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err19];
                                      } else {
                                        vErrors.push(err19);
                                      }
                                      errors++;
                                    }
                                    if ("number" !== data7) {
                                      const err20 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/NumberValue/properties/kind/const", keyword: "const", params: { allowedValue: "number" }, message: "must be equal to constant" };
                                      if (vErrors === null) {
                                        vErrors = [err20];
                                      } else {
                                        vErrors.push(err20);
                                      }
                                      errors++;
                                    }
                                    var valid9 = _errs30 === errors;
                                  } else {
                                    var valid9 = true;
                                  }
                                  if (valid9) {
                                    if (data1.unit !== void 0) {
                                      let data8 = data1.unit;
                                      const _errs32 = errors;
                                      if (errors === _errs32) {
                                        if (typeof data8 === "string") {
                                          if (func1(data8) > 64) {
                                            const err21 = { instancePath: instancePath + "/items/" + i0 + "/unit", schemaPath: "#/$defs/NumberValue/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err21];
                                            } else {
                                              vErrors.push(err21);
                                            }
                                            errors++;
                                          } else {
                                            if (func1(data8) < 1) {
                                              const err22 = { instancePath: instancePath + "/items/" + i0 + "/unit", schemaPath: "#/$defs/NumberValue/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err22];
                                              } else {
                                                vErrors.push(err22);
                                              }
                                              errors++;
                                            }
                                          }
                                        } else {
                                          const err23 = { instancePath: instancePath + "/items/" + i0 + "/unit", schemaPath: "#/$defs/NumberValue/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err23];
                                          } else {
                                            vErrors.push(err23);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid9 = _errs32 === errors;
                                    } else {
                                      var valid9 = true;
                                    }
                                    if (valid9) {
                                      if (data1.value !== void 0) {
                                        let data9 = data1.value;
                                        const _errs34 = errors;
                                        if (errors === _errs34) {
                                          if (typeof data9 === "string") {
                                            if (func1(data9) > 427) {
                                              const err24 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/NumberValue/properties/value/maxLength", keyword: "maxLength", params: { limit: 427 }, message: "must NOT have more than 427 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err24];
                                              } else {
                                                vErrors.push(err24);
                                              }
                                              errors++;
                                            } else {
                                              if (!pattern14.test(data9)) {
                                                const err25 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/NumberValue/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$" }, message: 'must match pattern "^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$"' };
                                                if (vErrors === null) {
                                                  vErrors = [err25];
                                                } else {
                                                  vErrors.push(err25);
                                                }
                                                errors++;
                                              }
                                            }
                                          } else {
                                            const err26 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/NumberValue/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err26];
                                            } else {
                                              vErrors.push(err26);
                                            }
                                            errors++;
                                          }
                                        }
                                        var valid9 = _errs34 === errors;
                                      } else {
                                        var valid9 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              const err27 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/NumberValue/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                              if (vErrors === null) {
                                vErrors = [err27];
                              } else {
                                vErrors.push(err27);
                              }
                              errors++;
                            }
                          }
                          var _valid1 = _errs26 === errors;
                          if (_valid1 && valid3) {
                            valid3 = false;
                            passing0 = [passing0, 2];
                          } else {
                            if (_valid1) {
                              valid3 = true;
                              passing0 = 2;
                              if (props0 !== true) {
                                props0 = true;
                              }
                            }
                            const _errs36 = errors;
                            const _errs37 = errors;
                            if (errors === _errs37) {
                              if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                                let missing4;
                                if (data1.kind === void 0 && (missing4 = "kind") || data1.value === void 0 && (missing4 = "value")) {
                                  const err28 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/StringConstant/required", keyword: "required", params: { missingProperty: missing4 }, message: "must have required property '" + missing4 + "'" };
                                  if (vErrors === null) {
                                    vErrors = [err28];
                                  } else {
                                    vErrors.push(err28);
                                  }
                                  errors++;
                                } else {
                                  const _errs39 = errors;
                                  for (const key4 in data1) {
                                    if (!(key4 === "kind" || key4 === "value")) {
                                      const err29 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/StringConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key4 }, message: "must NOT have additional properties" };
                                      if (vErrors === null) {
                                        vErrors = [err29];
                                      } else {
                                        vErrors.push(err29);
                                      }
                                      errors++;
                                      break;
                                    }
                                  }
                                  if (_errs39 === errors) {
                                    if (data1.kind !== void 0) {
                                      let data10 = data1.kind;
                                      const _errs40 = errors;
                                      if (typeof data10 !== "string") {
                                        const err30 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/StringConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err30];
                                        } else {
                                          vErrors.push(err30);
                                        }
                                        errors++;
                                      }
                                      if ("string" !== data10) {
                                        const err31 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/StringConstant/properties/kind/const", keyword: "const", params: { allowedValue: "string" }, message: "must be equal to constant" };
                                        if (vErrors === null) {
                                          vErrors = [err31];
                                        } else {
                                          vErrors.push(err31);
                                        }
                                        errors++;
                                      }
                                      var valid11 = _errs40 === errors;
                                    } else {
                                      var valid11 = true;
                                    }
                                    if (valid11) {
                                      if (data1.value !== void 0) {
                                        let data11 = data1.value;
                                        const _errs42 = errors;
                                        if (errors === _errs42) {
                                          if (typeof data11 === "string") {
                                            if (func1(data11) > 4096) {
                                              const err32 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/StringConstant/properties/value/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err32];
                                              } else {
                                                vErrors.push(err32);
                                              }
                                              errors++;
                                            }
                                          } else {
                                            const err33 = { instancePath: instancePath + "/items/" + i0 + "/value", schemaPath: "#/$defs/StringConstant/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err33];
                                            } else {
                                              vErrors.push(err33);
                                            }
                                            errors++;
                                          }
                                        }
                                        var valid11 = _errs42 === errors;
                                      } else {
                                        var valid11 = true;
                                      }
                                    }
                                  }
                                }
                              } else {
                                const err34 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/StringConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                if (vErrors === null) {
                                  vErrors = [err34];
                                } else {
                                  vErrors.push(err34);
                                }
                                errors++;
                              }
                            }
                            var _valid1 = _errs36 === errors;
                            if (_valid1 && valid3) {
                              valid3 = false;
                              passing0 = [passing0, 3];
                            } else {
                              if (_valid1) {
                                valid3 = true;
                                passing0 = 3;
                                if (props0 !== true) {
                                  props0 = true;
                                }
                              }
                              const _errs44 = errors;
                              if (!validate28(data1, { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
                                errors = vErrors.length;
                              }
                              var _valid1 = _errs44 === errors;
                              if (_valid1 && valid3) {
                                valid3 = false;
                                passing0 = [passing0, 4];
                              } else {
                                if (_valid1) {
                                  valid3 = true;
                                  passing0 = 4;
                                  if (props0 !== true) {
                                    props0 = true;
                                  }
                                }
                              }
                            }
                          }
                        }
                        if (!valid3) {
                          const err35 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/properties/items/items/anyOf/0/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                          if (vErrors === null) {
                            vErrors = [err35];
                          } else {
                            vErrors.push(err35);
                          }
                          errors++;
                        } else {
                          errors = _errs7;
                          if (vErrors !== null) {
                            if (_errs7) {
                              vErrors.length = _errs7;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var _valid0 = _errs6 === errors;
                        valid2 = valid2 || _valid0;
                        const _errs46 = errors;
                        const _errs47 = errors;
                        if (errors === _errs47) {
                          if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                            let missing5;
                            if (data1.kind === void 0 && (missing5 = "kind") || data1.reason_code === void 0 && (missing5 = "reason_code") || data1.member_id === void 0 && (missing5 = "member_id")) {
                              const err36 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/MissingValue/required", keyword: "required", params: { missingProperty: missing5 }, message: "must have required property '" + missing5 + "'" };
                              if (vErrors === null) {
                                vErrors = [err36];
                              } else {
                                vErrors.push(err36);
                              }
                              errors++;
                            } else {
                              const _errs49 = errors;
                              for (const key5 in data1) {
                                if (!(key5 === "kind" || key5 === "member_id" || key5 === "reason_code")) {
                                  const err37 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/MissingValue/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key5 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err37];
                                  } else {
                                    vErrors.push(err37);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs49 === errors) {
                                if (data1.kind !== void 0) {
                                  let data12 = data1.kind;
                                  const _errs50 = errors;
                                  if (typeof data12 !== "string") {
                                    const err38 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/MissingValue/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err38];
                                    } else {
                                      vErrors.push(err38);
                                    }
                                    errors++;
                                  }
                                  if ("missing" !== data12) {
                                    const err39 = { instancePath: instancePath + "/items/" + i0 + "/kind", schemaPath: "#/$defs/MissingValue/properties/kind/const", keyword: "const", params: { allowedValue: "missing" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err39];
                                    } else {
                                      vErrors.push(err39);
                                    }
                                    errors++;
                                  }
                                  var valid13 = _errs50 === errors;
                                } else {
                                  var valid13 = true;
                                }
                                if (valid13) {
                                  if (data1.member_id !== void 0) {
                                    let data13 = data1.member_id;
                                    const _errs52 = errors;
                                    if (errors === _errs52) {
                                      if (typeof data13 === "string") {
                                        if (func1(data13) > 128) {
                                          const err40 = { instancePath: instancePath + "/items/" + i0 + "/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err40];
                                          } else {
                                            vErrors.push(err40);
                                          }
                                          errors++;
                                        } else {
                                          if (func1(data13) < 1) {
                                            const err41 = { instancePath: instancePath + "/items/" + i0 + "/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err41];
                                            } else {
                                              vErrors.push(err41);
                                            }
                                            errors++;
                                          } else {
                                            if (!pattern4.test(data13)) {
                                              const err42 = { instancePath: instancePath + "/items/" + i0 + "/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                              if (vErrors === null) {
                                                vErrors = [err42];
                                              } else {
                                                vErrors.push(err42);
                                              }
                                              errors++;
                                            }
                                          }
                                        }
                                      } else {
                                        const err43 = { instancePath: instancePath + "/items/" + i0 + "/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err43];
                                        } else {
                                          vErrors.push(err43);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid13 = _errs52 === errors;
                                  } else {
                                    var valid13 = true;
                                  }
                                  if (valid13) {
                                    if (data1.reason_code !== void 0) {
                                      let data14 = data1.reason_code;
                                      const _errs54 = errors;
                                      if (errors === _errs54) {
                                        if (typeof data14 === "string") {
                                          if (func1(data14) > 128) {
                                            const err44 = { instancePath: instancePath + "/items/" + i0 + "/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err44];
                                            } else {
                                              vErrors.push(err44);
                                            }
                                            errors++;
                                          } else {
                                            if (func1(data14) < 1) {
                                              const err45 = { instancePath: instancePath + "/items/" + i0 + "/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err45];
                                              } else {
                                                vErrors.push(err45);
                                              }
                                              errors++;
                                            } else {
                                              if (!pattern4.test(data14)) {
                                                const err46 = { instancePath: instancePath + "/items/" + i0 + "/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                if (vErrors === null) {
                                                  vErrors = [err46];
                                                } else {
                                                  vErrors.push(err46);
                                                }
                                                errors++;
                                              }
                                            }
                                          }
                                        } else {
                                          const err47 = { instancePath: instancePath + "/items/" + i0 + "/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err47];
                                          } else {
                                            vErrors.push(err47);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid13 = _errs54 === errors;
                                    } else {
                                      var valid13 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err48 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/$defs/MissingValue/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err48];
                            } else {
                              vErrors.push(err48);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs46 === errors;
                        valid2 = valid2 || _valid0;
                        if (_valid0) {
                          if (props0 !== true) {
                            props0 = true;
                          }
                        }
                        if (!valid2) {
                          const err49 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/properties/items/items/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err49];
                          } else {
                            vErrors.push(err49);
                          }
                          errors++;
                          validate32.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs5;
                          if (vErrors !== null) {
                            if (_errs5) {
                              vErrors.length = _errs5;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate32.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.kind !== void 0) {
                  let data15 = data.kind;
                  const _errs56 = errors;
                  if (typeof data15 !== "string") {
                    validate32.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("collection" !== data15) {
                    validate32.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "collection" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs56 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate32.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate32.errors = vErrors;
      return errors === 0;
    }
    validate32.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate27(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate27.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.port === void 0 && (missing0 = "port") || data.value === void 0 && (missing0 = "value")) {
            validate27.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "port" || key0 === "value")) {
                validate27.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.port !== void 0) {
                let data0 = data.port;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate27.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate27.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate27.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate27.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.value !== void 0) {
                  let data1 = data.value;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  let passing0 = null;
                  const _errs6 = errors;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.kind === void 0 && (missing1 = "kind") || data1.value === void 0 && (missing1 = "value")) {
                        const err0 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs9 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "kind" || key1 === "value")) {
                            const err1 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err1];
                            } else {
                              vErrors.push(err1);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs9 === errors) {
                          if (data1.kind !== void 0) {
                            let data2 = data1.kind;
                            const _errs10 = errors;
                            if (typeof data2 !== "string") {
                              const err2 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if ("boolean" !== data2) {
                              const err3 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/const", keyword: "const", params: { allowedValue: "boolean" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                            var valid3 = _errs10 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data1.value !== void 0) {
                              const _errs12 = errors;
                              if (typeof data1.value !== "boolean") {
                                const err4 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/BooleanConstant/properties/value/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                if (vErrors === null) {
                                  vErrors = [err4];
                                } else {
                                  vErrors.push(err4);
                                }
                                errors++;
                              }
                              var valid3 = _errs12 === errors;
                            } else {
                              var valid3 = true;
                            }
                          }
                        }
                      }
                    } else {
                      const err5 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs6 === errors;
                  if (_valid0) {
                    valid1 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs14 = errors;
                  const _errs15 = errors;
                  if (errors === _errs15) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing2;
                      if (data1.kind === void 0 && (missing2 = "kind") || data1.value === void 0 && (missing2 = "value")) {
                        const err6 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      } else {
                        const _errs17 = errors;
                        for (const key2 in data1) {
                          if (!(key2 === "kind" || key2 === "unit" || key2 === "value")) {
                            const err7 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs17 === errors) {
                          if (data1.kind !== void 0) {
                            let data4 = data1.kind;
                            const _errs18 = errors;
                            if (typeof data4 !== "string") {
                              const err8 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err8];
                              } else {
                                vErrors.push(err8);
                              }
                              errors++;
                            }
                            if ("integer" !== data4) {
                              const err9 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/const", keyword: "const", params: { allowedValue: "integer" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err9];
                              } else {
                                vErrors.push(err9);
                              }
                              errors++;
                            }
                            var valid5 = _errs18 === errors;
                          } else {
                            var valid5 = true;
                          }
                          if (valid5) {
                            if (data1.unit !== void 0) {
                              let data5 = data1.unit;
                              const _errs20 = errors;
                              if (errors === _errs20) {
                                if (typeof data5 === "string") {
                                  if (func1(data5) > 64) {
                                    const err10 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err10];
                                    } else {
                                      vErrors.push(err10);
                                    }
                                    errors++;
                                  } else {
                                    if (func1(data5) < 1) {
                                      const err11 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err11];
                                      } else {
                                        vErrors.push(err11);
                                      }
                                      errors++;
                                    }
                                  }
                                } else {
                                  const err12 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err12];
                                  } else {
                                    vErrors.push(err12);
                                  }
                                  errors++;
                                }
                              }
                              var valid5 = _errs20 === errors;
                            } else {
                              var valid5 = true;
                            }
                            if (valid5) {
                              if (data1.value !== void 0) {
                                let data6 = data1.value;
                                const _errs22 = errors;
                                if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                  const err13 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err13];
                                  } else {
                                    vErrors.push(err13);
                                  }
                                  errors++;
                                }
                                if (errors === _errs22) {
                                  if (typeof data6 == "number" && isFinite(data6)) {
                                    if (data6 > 9007199254740991 || isNaN(data6)) {
                                      const err14 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" };
                                      if (vErrors === null) {
                                        vErrors = [err14];
                                      } else {
                                        vErrors.push(err14);
                                      }
                                      errors++;
                                    } else {
                                      if (data6 < -9007199254740991 || isNaN(data6)) {
                                        const err15 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/minimum", keyword: "minimum", params: { comparison: ">=", limit: -9007199254740991 }, message: "must be >= -9007199254740991" };
                                        if (vErrors === null) {
                                          vErrors = [err15];
                                        } else {
                                          vErrors.push(err15);
                                        }
                                        errors++;
                                      }
                                    }
                                  }
                                }
                                var valid5 = _errs22 === errors;
                              } else {
                                var valid5 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      const err16 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err16];
                      } else {
                        vErrors.push(err16);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs14 === errors;
                  if (_valid0 && valid1) {
                    valid1 = false;
                    passing0 = [passing0, 1];
                  } else {
                    if (_valid0) {
                      valid1 = true;
                      passing0 = 1;
                      if (props0 !== true) {
                        props0 = true;
                      }
                    }
                    const _errs24 = errors;
                    const _errs25 = errors;
                    if (errors === _errs25) {
                      if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                        let missing3;
                        if (data1.kind === void 0 && (missing3 = "kind") || data1.value === void 0 && (missing3 = "value")) {
                          const err17 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                          if (vErrors === null) {
                            vErrors = [err17];
                          } else {
                            vErrors.push(err17);
                          }
                          errors++;
                        } else {
                          const _errs27 = errors;
                          for (const key3 in data1) {
                            if (!(key3 === "kind" || key3 === "unit" || key3 === "value")) {
                              const err18 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" };
                              if (vErrors === null) {
                                vErrors = [err18];
                              } else {
                                vErrors.push(err18);
                              }
                              errors++;
                              break;
                            }
                          }
                          if (_errs27 === errors) {
                            if (data1.kind !== void 0) {
                              let data7 = data1.kind;
                              const _errs28 = errors;
                              if (typeof data7 !== "string") {
                                const err19 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/NumberValue/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              if ("number" !== data7) {
                                const err20 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/NumberValue/properties/kind/const", keyword: "const", params: { allowedValue: "number" }, message: "must be equal to constant" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                              }
                              var valid7 = _errs28 === errors;
                            } else {
                              var valid7 = true;
                            }
                            if (valid7) {
                              if (data1.unit !== void 0) {
                                let data8 = data1.unit;
                                const _errs30 = errors;
                                if (errors === _errs30) {
                                  if (typeof data8 === "string") {
                                    if (func1(data8) > 64) {
                                      const err21 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err21];
                                      } else {
                                        vErrors.push(err21);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data8) < 1) {
                                        const err22 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err22];
                                        } else {
                                          vErrors.push(err22);
                                        }
                                        errors++;
                                      }
                                    }
                                  } else {
                                    const err23 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err23];
                                    } else {
                                      vErrors.push(err23);
                                    }
                                    errors++;
                                  }
                                }
                                var valid7 = _errs30 === errors;
                              } else {
                                var valid7 = true;
                              }
                              if (valid7) {
                                if (data1.value !== void 0) {
                                  let data9 = data1.value;
                                  const _errs32 = errors;
                                  if (errors === _errs32) {
                                    if (typeof data9 === "string") {
                                      if (func1(data9) > 427) {
                                        const err24 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/maxLength", keyword: "maxLength", params: { limit: 427 }, message: "must NOT have more than 427 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err24];
                                        } else {
                                          vErrors.push(err24);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern14.test(data9)) {
                                          const err25 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$" }, message: 'must match pattern "^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$"' };
                                          if (vErrors === null) {
                                            vErrors = [err25];
                                          } else {
                                            vErrors.push(err25);
                                          }
                                          errors++;
                                        }
                                      }
                                    } else {
                                      const err26 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err26];
                                      } else {
                                        vErrors.push(err26);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid7 = _errs32 === errors;
                                } else {
                                  var valid7 = true;
                                }
                              }
                            }
                          }
                        }
                      } else {
                        const err27 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err27];
                        } else {
                          vErrors.push(err27);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs24 === errors;
                    if (_valid0 && valid1) {
                      valid1 = false;
                      passing0 = [passing0, 2];
                    } else {
                      if (_valid0) {
                        valid1 = true;
                        passing0 = 2;
                        if (props0 !== true) {
                          props0 = true;
                        }
                      }
                      const _errs34 = errors;
                      const _errs35 = errors;
                      if (errors === _errs35) {
                        if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                          let missing4;
                          if (data1.kind === void 0 && (missing4 = "kind") || data1.value === void 0 && (missing4 = "value")) {
                            const err28 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/required", keyword: "required", params: { missingProperty: missing4 }, message: "must have required property '" + missing4 + "'" };
                            if (vErrors === null) {
                              vErrors = [err28];
                            } else {
                              vErrors.push(err28);
                            }
                            errors++;
                          } else {
                            const _errs37 = errors;
                            for (const key4 in data1) {
                              if (!(key4 === "kind" || key4 === "value")) {
                                const err29 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key4 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err29];
                                } else {
                                  vErrors.push(err29);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs37 === errors) {
                              if (data1.kind !== void 0) {
                                let data10 = data1.kind;
                                const _errs38 = errors;
                                if (typeof data10 !== "string") {
                                  const err30 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/StringConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err30];
                                  } else {
                                    vErrors.push(err30);
                                  }
                                  errors++;
                                }
                                if ("string" !== data10) {
                                  const err31 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/StringConstant/properties/kind/const", keyword: "const", params: { allowedValue: "string" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err31];
                                  } else {
                                    vErrors.push(err31);
                                  }
                                  errors++;
                                }
                                var valid9 = _errs38 === errors;
                              } else {
                                var valid9 = true;
                              }
                              if (valid9) {
                                if (data1.value !== void 0) {
                                  let data11 = data1.value;
                                  const _errs40 = errors;
                                  if (errors === _errs40) {
                                    if (typeof data11 === "string") {
                                      if (func1(data11) > 4096) {
                                        const err32 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/StringConstant/properties/value/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err32];
                                        } else {
                                          vErrors.push(err32);
                                        }
                                        errors++;
                                      }
                                    } else {
                                      const err33 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/StringConstant/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err33];
                                      } else {
                                        vErrors.push(err33);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid9 = _errs40 === errors;
                                } else {
                                  var valid9 = true;
                                }
                              }
                            }
                          }
                        } else {
                          const err34 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err34];
                          } else {
                            vErrors.push(err34);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs34 === errors;
                      if (_valid0 && valid1) {
                        valid1 = false;
                        passing0 = [passing0, 3];
                      } else {
                        if (_valid0) {
                          valid1 = true;
                          passing0 = 3;
                          if (props0 !== true) {
                            props0 = true;
                          }
                        }
                        const _errs42 = errors;
                        if (!validate28(data1, { instancePath: instancePath + "/value", parentData: data, parentDataProperty: "value", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
                          errors = vErrors.length;
                        }
                        var _valid0 = _errs42 === errors;
                        if (_valid0 && valid1) {
                          valid1 = false;
                          passing0 = [passing0, 4];
                        } else {
                          if (_valid0) {
                            valid1 = true;
                            passing0 = 4;
                            if (props0 !== true) {
                              props0 = true;
                            }
                          }
                          const _errs43 = errors;
                          if (!validate32(data1, { instancePath: instancePath + "/value", parentData: data, parentDataProperty: "value", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate32.errors : vErrors.concat(validate32.errors);
                            errors = vErrors.length;
                          }
                          var _valid0 = _errs43 === errors;
                          if (_valid0 && valid1) {
                            valid1 = false;
                            passing0 = [passing0, 5];
                          } else {
                            if (_valid0) {
                              valid1 = true;
                              passing0 = 5;
                              if (props0 !== true) {
                                props0 = true;
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                  if (!valid1) {
                    const err35 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err35];
                    } else {
                      vErrors.push(err35);
                    }
                    errors++;
                    validate27.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs5;
                    if (vErrors !== null) {
                      if (_errs5) {
                        vErrors.length = _errs5;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate27.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate27.errors = vErrors;
      return errors === 0;
    }
    validate27.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate26(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate26.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.inputs === void 0 && (missing0 = "inputs") || data.budget === void 0 && (missing0 = "budget") || data.draft === void 0 && (missing0 = "draft")) {
            validate26.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "budget" || key0 === "draft" || key0 === "inputs" || key0 === "limits" || key0 === "plan_sha256" || key0 === "schema_version")) {
                validate26.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.budget !== void 0) {
                let data0 = data.budget;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.limit === void 0 && (missing1 = "limit")) {
                      validate26.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/AttemptBudget/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "limit" || key1 === "max_attempts_per_activation")) {
                          validate26.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/AttemptBudget/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.limit !== void 0) {
                          let data1 = data0.limit;
                          const _errs6 = errors;
                          if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                            validate26.errors = [{ instancePath: instancePath + "/budget/limit", schemaPath: "#/$defs/AttemptBudget/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs6) {
                            if (typeof data1 == "number" && isFinite(data1)) {
                              if (data1 > 9007199254740991 || isNaN(data1)) {
                                validate26.errors = [{ instancePath: instancePath + "/budget/limit", schemaPath: "#/$defs/AttemptBudget/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data1 < 1 || isNaN(data1)) {
                                  validate26.errors = [{ instancePath: instancePath + "/budget/limit", schemaPath: "#/$defs/AttemptBudget/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                  return false;
                                }
                              }
                            }
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.max_attempts_per_activation !== void 0) {
                            let data2 = data0.max_attempts_per_activation;
                            const _errs8 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              validate26.errors = [{ instancePath: instancePath + "/budget/max_attempts_per_activation", schemaPath: "#/$defs/AttemptBudget/properties/max_attempts_per_activation/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (errors === _errs8) {
                              if (typeof data2 == "number" && isFinite(data2)) {
                                if (data2 > 100 || isNaN(data2)) {
                                  validate26.errors = [{ instancePath: instancePath + "/budget/max_attempts_per_activation", schemaPath: "#/$defs/AttemptBudget/properties/max_attempts_per_activation/maximum", keyword: "maximum", params: { comparison: "<=", limit: 100 }, message: "must be <= 100" }];
                                  return false;
                                } else {
                                  if (data2 < 1 || isNaN(data2)) {
                                    validate26.errors = [{ instancePath: instancePath + "/budget/max_attempts_per_activation", schemaPath: "#/$defs/AttemptBudget/properties/max_attempts_per_activation/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                    return false;
                                  }
                                }
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                        }
                      }
                    }
                  } else {
                    validate26.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/AttemptBudget/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.draft !== void 0) {
                  let data3 = data.draft;
                  const _errs10 = errors;
                  const _errs11 = errors;
                  if (errors === _errs11) {
                    if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                      let missing2;
                      if (data3.draft_id === void 0 && (missing2 = "draft_id") || data3.revision === void 0 && (missing2 = "revision") || data3.content_sha256 === void 0 && (missing2 = "content_sha256") || data3.validation_id === void 0 && (missing2 = "validation_id") || data3.universe_sha256 === void 0 && (missing2 = "universe_sha256")) {
                        validate26.errors = [{ instancePath: instancePath + "/draft", schemaPath: "#/$defs/DraftSelection/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                        return false;
                      } else {
                        const _errs13 = errors;
                        for (const key2 in data3) {
                          if (!(key2 === "content_sha256" || key2 === "draft_id" || key2 === "revision" || key2 === "universe_sha256" || key2 === "validation_id")) {
                            validate26.errors = [{ instancePath: instancePath + "/draft", schemaPath: "#/$defs/DraftSelection/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs13 === errors) {
                          if (data3.content_sha256 !== void 0) {
                            let data4 = data3.content_sha256;
                            const _errs14 = errors;
                            if (errors === _errs14) {
                              if (typeof data4 === "string") {
                                if (!pattern9.test(data4)) {
                                  validate26.errors = [{ instancePath: instancePath + "/draft/content_sha256", schemaPath: "#/$defs/DraftSelection/properties/content_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate26.errors = [{ instancePath: instancePath + "/draft/content_sha256", schemaPath: "#/$defs/DraftSelection/properties/content_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid4 = _errs14 === errors;
                          } else {
                            var valid4 = true;
                          }
                          if (valid4) {
                            if (data3.draft_id !== void 0) {
                              let data5 = data3.draft_id;
                              const _errs16 = errors;
                              if (errors === _errs16) {
                                if (typeof data5 === "string") {
                                  if (func1(data5) > 128) {
                                    validate26.errors = [{ instancePath: instancePath + "/draft/draft_id", schemaPath: "#/$defs/DraftSelection/properties/draft_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data5) < 1) {
                                      validate26.errors = [{ instancePath: instancePath + "/draft/draft_id", schemaPath: "#/$defs/DraftSelection/properties/draft_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data5)) {
                                        validate26.errors = [{ instancePath: instancePath + "/draft/draft_id", schemaPath: "#/$defs/DraftSelection/properties/draft_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate26.errors = [{ instancePath: instancePath + "/draft/draft_id", schemaPath: "#/$defs/DraftSelection/properties/draft_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid4 = _errs16 === errors;
                            } else {
                              var valid4 = true;
                            }
                            if (valid4) {
                              if (data3.revision !== void 0) {
                                let data6 = data3.revision;
                                const _errs18 = errors;
                                if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                  validate26.errors = [{ instancePath: instancePath + "/draft/revision", schemaPath: "#/$defs/DraftSelection/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (errors === _errs18) {
                                  if (typeof data6 == "number" && isFinite(data6)) {
                                    if (data6 > 9007199254740991 || isNaN(data6)) {
                                      validate26.errors = [{ instancePath: instancePath + "/draft/revision", schemaPath: "#/$defs/DraftSelection/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                      return false;
                                    } else {
                                      if (data6 < 1 || isNaN(data6)) {
                                        validate26.errors = [{ instancePath: instancePath + "/draft/revision", schemaPath: "#/$defs/DraftSelection/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                        return false;
                                      }
                                    }
                                  }
                                }
                                var valid4 = _errs18 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data3.universe_sha256 !== void 0) {
                                  let data7 = data3.universe_sha256;
                                  const _errs20 = errors;
                                  if (errors === _errs20) {
                                    if (typeof data7 === "string") {
                                      if (!pattern9.test(data7)) {
                                        validate26.errors = [{ instancePath: instancePath + "/draft/universe_sha256", schemaPath: "#/$defs/DraftSelection/properties/universe_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate26.errors = [{ instancePath: instancePath + "/draft/universe_sha256", schemaPath: "#/$defs/DraftSelection/properties/universe_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs20 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data3.validation_id !== void 0) {
                                    let data8 = data3.validation_id;
                                    const _errs22 = errors;
                                    if (errors === _errs22) {
                                      if (typeof data8 === "string") {
                                        if (func1(data8) > 128) {
                                          validate26.errors = [{ instancePath: instancePath + "/draft/validation_id", schemaPath: "#/$defs/DraftSelection/properties/validation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data8) < 1) {
                                            validate26.errors = [{ instancePath: instancePath + "/draft/validation_id", schemaPath: "#/$defs/DraftSelection/properties/validation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data8)) {
                                              validate26.errors = [{ instancePath: instancePath + "/draft/validation_id", schemaPath: "#/$defs/DraftSelection/properties/validation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate26.errors = [{ instancePath: instancePath + "/draft/validation_id", schemaPath: "#/$defs/DraftSelection/properties/validation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid4 = _errs22 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate26.errors = [{ instancePath: instancePath + "/draft", schemaPath: "#/$defs/DraftSelection/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.inputs !== void 0) {
                    let data9 = data.inputs;
                    const _errs24 = errors;
                    if (errors === _errs24) {
                      if (Array.isArray(data9)) {
                        if (data9.length > 64) {
                          validate26.errors = [{ instancePath: instancePath + "/inputs", schemaPath: "#/properties/inputs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                          return false;
                        } else {
                          var valid5 = true;
                          const len0 = data9.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs26 = errors;
                            if (!validate27(data9[i0], { instancePath: instancePath + "/inputs/" + i0, parentData: data9, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
                              errors = vErrors.length;
                            }
                            var valid5 = _errs26 === errors;
                            if (!valid5) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate26.errors = [{ instancePath: instancePath + "/inputs", schemaPath: "#/properties/inputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs24 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.limits !== void 0) {
                      let data11 = data.limits;
                      const _errs27 = errors;
                      const _errs28 = errors;
                      if (errors === _errs28) {
                        if (data11 && typeof data11 == "object" && !Array.isArray(data11)) {
                          const _errs30 = errors;
                          for (const key3 in data11) {
                            if (!(key3 === "deadline_seconds" || key3 === "max_activations")) {
                              validate26.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/GraphLimits/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs30 === errors) {
                            if (data11.deadline_seconds !== void 0) {
                              let data12 = data11.deadline_seconds;
                              const _errs31 = errors;
                              if (!(typeof data12 == "number" && (!(data12 % 1) && !isNaN(data12)) && isFinite(data12))) {
                                validate26.errors = [{ instancePath: instancePath + "/limits/deadline_seconds", schemaPath: "#/$defs/GraphLimits/properties/deadline_seconds/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs31) {
                                if (typeof data12 == "number" && isFinite(data12)) {
                                  if (data12 > 86400 || isNaN(data12)) {
                                    validate26.errors = [{ instancePath: instancePath + "/limits/deadline_seconds", schemaPath: "#/$defs/GraphLimits/properties/deadline_seconds/maximum", keyword: "maximum", params: { comparison: "<=", limit: 86400 }, message: "must be <= 86400" }];
                                    return false;
                                  } else {
                                    if (data12 < 1 || isNaN(data12)) {
                                      validate26.errors = [{ instancePath: instancePath + "/limits/deadline_seconds", schemaPath: "#/$defs/GraphLimits/properties/deadline_seconds/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                      return false;
                                    }
                                  }
                                }
                              }
                              var valid7 = _errs31 === errors;
                            } else {
                              var valid7 = true;
                            }
                            if (valid7) {
                              if (data11.max_activations !== void 0) {
                                let data13 = data11.max_activations;
                                const _errs33 = errors;
                                if (!(typeof data13 == "number" && (!(data13 % 1) && !isNaN(data13)) && isFinite(data13))) {
                                  validate26.errors = [{ instancePath: instancePath + "/limits/max_activations", schemaPath: "#/$defs/GraphLimits/properties/max_activations/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (errors === _errs33) {
                                  if (typeof data13 == "number" && isFinite(data13)) {
                                    if (data13 > 1e5 || isNaN(data13)) {
                                      validate26.errors = [{ instancePath: instancePath + "/limits/max_activations", schemaPath: "#/$defs/GraphLimits/properties/max_activations/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                                      return false;
                                    } else {
                                      if (data13 < 1 || isNaN(data13)) {
                                        validate26.errors = [{ instancePath: instancePath + "/limits/max_activations", schemaPath: "#/$defs/GraphLimits/properties/max_activations/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                        return false;
                                      }
                                    }
                                  }
                                }
                                var valid7 = _errs33 === errors;
                              } else {
                                var valid7 = true;
                              }
                            }
                          }
                        } else {
                          validate26.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/GraphLimits/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs27 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.plan_sha256 !== void 0) {
                        let data14 = data.plan_sha256;
                        const _errs35 = errors;
                        if (errors === _errs35) {
                          if (typeof data14 === "string") {
                            if (!pattern9.test(data14)) {
                              validate26.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate26.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs35 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.schema_version !== void 0) {
                          let data15 = data.schema_version;
                          const _errs37 = errors;
                          if (typeof data15 !== "string") {
                            validate26.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data15) {
                            validate26.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs37 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate26.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate26.errors = vErrors;
      return errors === 0;
    }
    validate26.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate24(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate24.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.identity === void 0 && (missing0 = "identity") || data.payload === void 0 && (missing0 = "payload") || data.encoding === void 0 && (missing0 = "encoding")) {
            validate24.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "encoding" || key0 === "identity" || key0 === "payload")) {
                validate24.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.encoding !== void 0) {
                let data0 = data.encoding;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate24.errors = [{ instancePath: instancePath + "/encoding", schemaPath: "#/properties/encoding/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("amphora-command-v2" !== data0) {
                  validate24.errors = [{ instancePath: instancePath + "/encoding", schemaPath: "#/properties/encoding/const", keyword: "const", params: { allowedValue: "amphora-command-v2" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.identity !== void 0) {
                  const _errs4 = errors;
                  if (!validate21(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.payload !== void 0) {
                    const _errs5 = errors;
                    if (!validate26(data.payload, { instancePath: instancePath + "/payload", parentData: data, parentDataProperty: "payload", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate24.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate24.errors = vErrors;
      return errors === 0;
    }
    validate24.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate38(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate38.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.identity === void 0 && (missing0 = "identity") || data.payload === void 0 && (missing0 = "payload")) {
            validate38.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "identity" || key0 === "payload")) {
                validate38.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.identity !== void 0) {
                const _errs2 = errors;
                if (!validate21(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.payload !== void 0) {
                  const _errs3 = errors;
                  if (!validate26(data.payload, { instancePath: instancePath + "/payload", parentData: data, parentDataProperty: "payload", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate38.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate38.errors = vErrors;
      return errors === 0;
    }
    validate38.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate23(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate23.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.profile === void 0 && (missing0 = "profile") || data.admission === void 0 && (missing0 = "admission")) {
            validate23.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "admission" || key0 === "profile")) {
                validate23.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.admission !== void 0) {
                let data0 = data.admission;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate24(data0, { instancePath: instancePath + "/admission", parentData: data, parentDataProperty: "admission", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                if (_valid0) {
                  var props0 = true;
                }
                const _errs5 = errors;
                if (!validate38(data0, { instancePath: instancePath + "/admission", parentData: data, parentDataProperty: "admission", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate38.errors : vErrors.concat(validate38.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs5 === errors;
                valid1 = valid1 || _valid0;
                if (_valid0) {
                  if (props0 !== true) {
                    props0 = true;
                  }
                }
                if (!valid1) {
                  const err0 = { instancePath: instancePath + "/admission", schemaPath: "#/properties/admission/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                  validate23.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.profile !== void 0) {
                  let data1 = data.profile;
                  const _errs6 = errors;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.profile_id === void 0 && (missing1 = "profile_id") || data1.version === void 0 && (missing1 = "version") || data1.sha256 === void 0 && (missing1 = "sha256")) {
                        validate23.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/$defs/LaunchProfileRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs9 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "profile_id" || key1 === "sha256" || key1 === "version")) {
                            validate23.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/$defs/LaunchProfileRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs9 === errors) {
                          if (data1.profile_id !== void 0) {
                            let data2 = data1.profile_id;
                            const _errs10 = errors;
                            if (errors === _errs10) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate23.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate23.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate23.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate23.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid3 = _errs10 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data1.sha256 !== void 0) {
                              let data3 = data1.sha256;
                              const _errs12 = errors;
                              if (errors === _errs12) {
                                if (typeof data3 === "string") {
                                  if (!pattern9.test(data3)) {
                                    validate23.errors = [{ instancePath: instancePath + "/profile/sha256", schemaPath: "#/$defs/LaunchProfileRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate23.errors = [{ instancePath: instancePath + "/profile/sha256", schemaPath: "#/$defs/LaunchProfileRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid3 = _errs12 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data1.version !== void 0) {
                                let data4 = data1.version;
                                const _errs14 = errors;
                                if (typeof data4 !== "string") {
                                  validate23.errors = [{ instancePath: instancePath + "/profile/version", schemaPath: "#/$defs/LaunchProfileRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data4) {
                                  validate23.errors = [{ instancePath: instancePath + "/profile/version", schemaPath: "#/$defs/LaunchProfileRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid3 = _errs14 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate23.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/$defs/LaunchProfileRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs6 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate23.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate23.errors = vErrors;
      return errors === 0;
    }
    validate23.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate20(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate20.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.encoding === void 0 && (missing0 = "encoding") || data.identity === void 0 && (missing0 = "identity") || data.payload === void 0 && (missing0 = "payload")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "encoding" || key0 === "identity" || key0 === "payload")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.encoding !== void 0) {
                let data0 = data.encoding;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate20.errors = [{ instancePath: instancePath + "/encoding", schemaPath: "#/properties/encoding/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("amphora-command-v2" !== data0) {
                  validate20.errors = [{ instancePath: instancePath + "/encoding", schemaPath: "#/properties/encoding/const", keyword: "const", params: { allowedValue: "amphora-command-v2" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.identity !== void 0) {
                  const _errs4 = errors;
                  if (!validate21(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.payload !== void 0) {
                    const _errs5 = errors;
                    if (!validate23(data.payload, { instancePath: instancePath + "/payload", parentData: data, parentDataProperty: "payload", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate20.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate20.errors = vErrors;
      return errors === 0;
    }
    validate20.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.receipt = validate43;
    var schema57 = { "$defs": { "AcceptedReceipt": { "additionalProperties": false, "properties": { "binding": { "$ref": "#/$defs/ReceiptBinding" }, "committed": { "$ref": "#/$defs/CommittedReference" }, "status": { "const": "accepted", "title": "Status", "type": "string" } }, "required": ["status", "binding", "committed"], "title": "AcceptedReceipt", "type": "object" }, "CommandIdentity": { "additionalProperties": false, "properties": { "actor_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Actor Id", "type": "string" }, "command_family": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Command Family", "type": "string" }, "command_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Command Id", "type": "string" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["command_family", "command_id", "scope", "actor_id"], "title": "CommandIdentity", "type": "object" }, "CommandReceipt": { "additionalProperties": false, "properties": { "outcome": { "discriminator": { "mapping": { "accepted": "#/$defs/AcceptedReceipt", "pending": "#/$defs/PendingReceipt", "rejected": "#/$defs/RejectedReceipt" }, "propertyName": "status" }, "oneOf": [{ "$ref": "#/$defs/PendingReceipt" }, { "$ref": "#/$defs/AcceptedReceipt" }, { "$ref": "#/$defs/RejectedReceipt" }], "title": "Outcome" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" } }, "required": ["outcome"], "title": "CommandReceipt", "type": "object" }, "CommittedReference": { "additionalProperties": false, "properties": { "kind": { "enum": ["run", "attempt", "completion", "worker_policy"], "title": "Kind", "type": "string" }, "object_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Object Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Revision", "type": "integer" } }, "required": ["kind", "object_id", "revision"], "title": "CommittedReference", "type": "object" }, "LaunchProfileRef": { "additionalProperties": false, "properties": { "profile_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Profile Id", "type": "string" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "version": { "const": "1", "title": "Version", "type": "string" } }, "required": ["profile_id", "version", "sha256"], "title": "LaunchProfileRef", "type": "object" }, "PendingReceipt": { "additionalProperties": false, "properties": { "binding": { "$ref": "#/$defs/ReceiptBinding" }, "status": { "const": "pending", "title": "Status", "type": "string" } }, "required": ["status", "binding"], "title": "PendingReceipt", "type": "object" }, "ReceiptBinding": { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/CommandIdentity" }, "operation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Operation Id", "type": "string" }, "request_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Request Sha256", "type": "string" } }, "required": ["identity", "request_sha256", "operation_id"], "title": "ReceiptBinding", "type": "object" }, "RejectedReceipt": { "additionalProperties": false, "properties": { "binding": { "$ref": "#/$defs/ReceiptBinding" }, "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" }, "status": { "const": "rejected", "title": "Status", "type": "string" } }, "required": ["status", "binding", "reason_code"], "title": "RejectedReceipt", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" }, "WorkerReadiness": { "additionalProperties": false, "properties": { "expected": { "maximum": 64, "minimum": 0, "title": "Expected", "type": "integer" }, "ready": { "maximum": 64, "minimum": 0, "title": "Ready", "type": "integer" } }, "required": ["expected", "ready"], "title": "WorkerReadiness", "type": "object" } }, "$id": "urn:amphora:campaign-launch.receipt:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "admission": { "anyOf": [{ "$ref": "#/$defs/CommandReceipt" }, { "type": "null" }] }, "created_at": { "format": "date-time", "title": "Created At", "type": "string" }, "identity": { "$ref": "#/$defs/CommandIdentity" }, "phase": { "enum": ["preparing", "admission_unresolved", "rejected", "admitted_not_engaged", "engaging", "engaged", "draining", "released", "recovery_required"], "title": "Phase", "type": "string" }, "profile": { "$ref": "#/$defs/LaunchProfileRef" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" }, "request_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Request Sha256", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Revision", "type": "integer" }, "run_id": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Run Id" }, "updated_at": { "format": "date-time", "title": "Updated At", "type": "string" }, "wire_version": { "const": "1", "default": "1", "title": "Wire Version", "type": "string" }, "workers": { "$ref": "#/$defs/WorkerReadiness" } }, "required": ["identity", "request_sha256", "profile", "revision", "phase", "reason_code", "created_at", "updated_at", "admission", "run_id", "workers"], "title": "LaunchReceipt", "type": "object" };
    var func49 = Object.prototype.hasOwnProperty;
    function validate47(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate47.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.command_family === void 0 && (missing0 = "command_family") || data.command_id === void 0 && (missing0 = "command_id") || data.scope === void 0 && (missing0 = "scope") || data.actor_id === void 0 && (missing0 = "actor_id")) {
            validate47.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "actor_id" || key0 === "command_family" || key0 === "command_id" || key0 === "schema_version" || key0 === "scope")) {
                validate47.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.actor_id !== void 0) {
                let data0 = data.actor_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate47.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate47.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate47.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate47.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.command_family !== void 0) {
                  let data1 = data.command_family;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate47.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate47.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate47.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate47.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.command_id !== void 0) {
                    let data2 = data.command_id;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          validate47.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate47.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern4.test(data2)) {
                              validate47.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate47.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.schema_version !== void 0) {
                      let data3 = data.schema_version;
                      const _errs8 = errors;
                      if (typeof data3 !== "string") {
                        validate47.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data3) {
                        validate47.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope !== void 0) {
                        let data4 = data.scope;
                        const _errs10 = errors;
                        const _errs11 = errors;
                        if (errors === _errs11) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.tenant_id === void 0 && (missing1 = "tenant_id") || data4.project_id === void 0 && (missing1 = "project_id")) {
                              validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs13 === errors) {
                                if (data4.project_id !== void 0) {
                                  let data5 = data4.project_id;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 128) {
                                        validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
                                            validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data4.tenant_id !== void 0) {
                                    let data6 = data4.tenant_id;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 === "string") {
                                        if (func1(data6) > 128) {
                                          validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
                                              validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid2 = _errs16 === errors;
                                  } else {
                                    var valid2 = true;
                                  }
                                }
                              }
                            }
                          } else {
                            validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs10 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate47.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate47.errors = vErrors;
      return errors === 0;
    }
    validate47.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate46(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate46.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.identity === void 0 && (missing0 = "identity") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.operation_id === void 0 && (missing0 = "operation_id")) {
            validate46.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "identity" || key0 === "operation_id" || key0 === "request_sha256")) {
                validate46.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.identity !== void 0) {
                const _errs2 = errors;
                if (!validate47(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.operation_id !== void 0) {
                  let data1 = data.operation_id;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate46.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate46.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate46.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate46.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.request_sha256 !== void 0) {
                    let data2 = data.request_sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern9.test(data2)) {
                          validate46.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate46.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate46.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate46.errors = vErrors;
      return errors === 0;
    }
    validate46.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate45(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate45.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.binding === void 0 && (missing0 = "binding")) {
            validate45.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "status")) {
                validate45.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate46(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate46.errors : vErrors.concat(validate46.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.status !== void 0) {
                  let data1 = data.status;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate45.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("pending" !== data1) {
                    validate45.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "pending" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate45.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate45.errors = vErrors;
      return errors === 0;
    }
    validate45.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema64 = { "additionalProperties": false, "properties": { "kind": { "enum": ["run", "attempt", "completion", "worker_policy"], "title": "Kind", "type": "string" }, "object_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Object Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Revision", "type": "integer" } }, "required": ["kind", "object_id", "revision"], "title": "CommittedReference", "type": "object" };
    function validate51(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate51.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.binding === void 0 && (missing0 = "binding") || data.committed === void 0 && (missing0 = "committed")) {
            validate51.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "committed" || key0 === "status")) {
                validate51.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate46(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate46.errors : vErrors.concat(validate46.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.committed !== void 0) {
                  let data1 = data.committed;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.kind === void 0 && (missing1 = "kind") || data1.object_id === void 0 && (missing1 = "object_id") || data1.revision === void 0 && (missing1 = "revision")) {
                        validate51.errors = [{ instancePath: instancePath + "/committed", schemaPath: "#/$defs/CommittedReference/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs6 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "kind" || key1 === "object_id" || key1 === "revision")) {
                            validate51.errors = [{ instancePath: instancePath + "/committed", schemaPath: "#/$defs/CommittedReference/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs6 === errors) {
                          if (data1.kind !== void 0) {
                            let data2 = data1.kind;
                            const _errs7 = errors;
                            if (typeof data2 !== "string") {
                              validate51.errors = [{ instancePath: instancePath + "/committed/kind", schemaPath: "#/$defs/CommittedReference/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if (!(data2 === "run" || data2 === "attempt" || data2 === "completion" || data2 === "worker_policy")) {
                              validate51.errors = [{ instancePath: instancePath + "/committed/kind", schemaPath: "#/$defs/CommittedReference/properties/kind/enum", keyword: "enum", params: { allowedValues: schema64.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                              return false;
                            }
                            var valid2 = _errs7 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.object_id !== void 0) {
                              let data3 = data1.object_id;
                              const _errs9 = errors;
                              if (errors === _errs9) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate51.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/CommittedReference/properties/object_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate51.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/CommittedReference/properties/object_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate51.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/CommittedReference/properties/object_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate51.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/CommittedReference/properties/object_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs9 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data1.revision !== void 0) {
                                let data4 = data1.revision;
                                const _errs11 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  validate51.errors = [{ instancePath: instancePath + "/committed/revision", schemaPath: "#/$defs/CommittedReference/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (errors === _errs11) {
                                  if (typeof data4 == "number" && isFinite(data4)) {
                                    if (data4 > 9007199254740991 || isNaN(data4)) {
                                      validate51.errors = [{ instancePath: instancePath + "/committed/revision", schemaPath: "#/$defs/CommittedReference/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                      return false;
                                    } else {
                                      if (data4 < 0 || isNaN(data4)) {
                                        validate51.errors = [{ instancePath: instancePath + "/committed/revision", schemaPath: "#/$defs/CommittedReference/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                        return false;
                                      }
                                    }
                                  }
                                }
                                var valid2 = _errs11 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate51.errors = [{ instancePath: instancePath + "/committed", schemaPath: "#/$defs/CommittedReference/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data5 = data.status;
                    const _errs13 = errors;
                    if (typeof data5 !== "string") {
                      validate51.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("accepted" !== data5) {
                      validate51.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "accepted" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate51.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate51.errors = vErrors;
      return errors === 0;
    }
    validate51.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate54(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate54.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.binding === void 0 && (missing0 = "binding") || data.reason_code === void 0 && (missing0 = "reason_code")) {
            validate54.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "reason_code" || key0 === "status")) {
                validate54.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate46(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate46.errors : vErrors.concat(validate46.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reason_code !== void 0) {
                  let data1 = data.reason_code;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate54.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate54.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate54.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate54.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data2 = data.status;
                    const _errs5 = errors;
                    if (typeof data2 !== "string") {
                      validate54.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("rejected" !== data2) {
                      validate54.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "rejected" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate54.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate54.errors = vErrors;
      return errors === 0;
    }
    validate54.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate44(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate44.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.outcome === void 0 && (missing0 = "outcome")) {
            validate44.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "outcome" || key0 === "schema_version")) {
                validate44.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.outcome !== void 0) {
                let data0 = data.outcome;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                let passing0 = null;
                const _errs4 = errors;
                if (!validate45(data0, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate45.errors : vErrors.concat(validate45.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                if (_valid0) {
                  valid1 = true;
                  passing0 = 0;
                  var props0 = true;
                }
                const _errs5 = errors;
                if (!validate51(data0, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate51.errors : vErrors.concat(validate51.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs5 === errors;
                if (_valid0 && valid1) {
                  valid1 = false;
                  passing0 = [passing0, 1];
                } else {
                  if (_valid0) {
                    valid1 = true;
                    passing0 = 1;
                    if (props0 !== true) {
                      props0 = true;
                    }
                  }
                  const _errs6 = errors;
                  if (!validate54(data0, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate54.errors : vErrors.concat(validate54.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
                  if (_valid0 && valid1) {
                    valid1 = false;
                    passing0 = [passing0, 2];
                  } else {
                    if (_valid0) {
                      valid1 = true;
                      passing0 = 2;
                      if (props0 !== true) {
                        props0 = true;
                      }
                    }
                  }
                }
                if (!valid1) {
                  const err0 = { instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                  validate44.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.schema_version !== void 0) {
                  let data1 = data.schema_version;
                  const _errs8 = errors;
                  if (typeof data1 !== "string") {
                    validate44.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("1" !== data1) {
                    validate44.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate44.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate44.errors = vErrors;
      return errors === 0;
    }
    validate44.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var formats0 = require_formats().fullFormats["date-time"];
    function validate43(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate43.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.identity === void 0 && (missing0 = "identity") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.profile === void 0 && (missing0 = "profile") || data.revision === void 0 && (missing0 = "revision") || data.phase === void 0 && (missing0 = "phase") || data.reason_code === void 0 && (missing0 = "reason_code") || data.created_at === void 0 && (missing0 = "created_at") || data.updated_at === void 0 && (missing0 = "updated_at") || data.admission === void 0 && (missing0 = "admission") || data.run_id === void 0 && (missing0 = "run_id") || data.workers === void 0 && (missing0 = "workers")) {
            validate43.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func49.call(schema57.properties, key0)) {
                validate43.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.admission !== void 0) {
                let data0 = data.admission;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate44(data0, { instancePath: instancePath + "/admission", parentData: data, parentDataProperty: "admission", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate44.errors : vErrors.concat(validate44.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/admission", schemaPath: "#/properties/admission/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs5 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err1 = { instancePath: instancePath + "/admission", schemaPath: "#/properties/admission/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate43.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.created_at !== void 0) {
                  let data1 = data.created_at;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (errors === _errs7) {
                      if (typeof data1 === "string") {
                        if (!formats0.validate(data1)) {
                          validate43.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/format", keyword: "format", params: { format: "date-time" }, message: 'must match format "date-time"' }];
                          return false;
                        }
                      } else {
                        validate43.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.identity !== void 0) {
                    const _errs9 = errors;
                    if (!validate47(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.phase !== void 0) {
                      let data3 = data.phase;
                      const _errs10 = errors;
                      if (typeof data3 !== "string") {
                        validate43.errors = [{ instancePath: instancePath + "/phase", schemaPath: "#/properties/phase/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data3 === "preparing" || data3 === "admission_unresolved" || data3 === "rejected" || data3 === "admitted_not_engaged" || data3 === "engaging" || data3 === "engaged" || data3 === "draining" || data3 === "released" || data3 === "recovery_required")) {
                        validate43.errors = [{ instancePath: instancePath + "/phase", schemaPath: "#/properties/phase/enum", keyword: "enum", params: { allowedValues: schema57.properties.phase.enum }, message: "must be equal to one of the allowed values" }];
                        return false;
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.profile !== void 0) {
                        let data4 = data.profile;
                        const _errs12 = errors;
                        const _errs13 = errors;
                        if (errors === _errs13) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.profile_id === void 0 && (missing1 = "profile_id") || data4.version === void 0 && (missing1 = "version") || data4.sha256 === void 0 && (missing1 = "sha256")) {
                              validate43.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/$defs/LaunchProfileRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs15 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "profile_id" || key1 === "sha256" || key1 === "version")) {
                                  validate43.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/$defs/LaunchProfileRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs15 === errors) {
                                if (data4.profile_id !== void 0) {
                                  let data5 = data4.profile_id;
                                  const _errs16 = errors;
                                  if (errors === _errs16) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 128) {
                                        validate43.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate43.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
                                            validate43.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate43.errors = [{ instancePath: instancePath + "/profile/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid3 = _errs16 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data4.sha256 !== void 0) {
                                    let data6 = data4.sha256;
                                    const _errs18 = errors;
                                    if (errors === _errs18) {
                                      if (typeof data6 === "string") {
                                        if (!pattern9.test(data6)) {
                                          validate43.errors = [{ instancePath: instancePath + "/profile/sha256", schemaPath: "#/$defs/LaunchProfileRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                          return false;
                                        }
                                      } else {
                                        validate43.errors = [{ instancePath: instancePath + "/profile/sha256", schemaPath: "#/$defs/LaunchProfileRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid3 = _errs18 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data4.version !== void 0) {
                                      let data7 = data4.version;
                                      const _errs20 = errors;
                                      if (typeof data7 !== "string") {
                                        validate43.errors = [{ instancePath: instancePath + "/profile/version", schemaPath: "#/$defs/LaunchProfileRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("1" !== data7) {
                                        validate43.errors = [{ instancePath: instancePath + "/profile/version", schemaPath: "#/$defs/LaunchProfileRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid3 = _errs20 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            validate43.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/$defs/LaunchProfileRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs12 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.reason_code !== void 0) {
                          let data8 = data.reason_code;
                          const _errs22 = errors;
                          const _errs23 = errors;
                          let valid4 = false;
                          const _errs24 = errors;
                          if (errors === _errs24) {
                            if (typeof data8 === "string") {
                              if (func1(data8) > 128) {
                                const err2 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              } else {
                                if (func1(data8) < 1) {
                                  const err3 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                } else {
                                  if (!pattern4.test(data8)) {
                                    const err4 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                    if (vErrors === null) {
                                      vErrors = [err4];
                                    } else {
                                      vErrors.push(err4);
                                    }
                                    errors++;
                                  }
                                }
                              }
                            } else {
                              const err5 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err5];
                              } else {
                                vErrors.push(err5);
                              }
                              errors++;
                            }
                          }
                          var _valid1 = _errs24 === errors;
                          valid4 = valid4 || _valid1;
                          const _errs26 = errors;
                          if (data8 !== null) {
                            const err6 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          }
                          var _valid1 = _errs26 === errors;
                          valid4 = valid4 || _valid1;
                          if (!valid4) {
                            const err7 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                            validate43.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs23;
                            if (vErrors !== null) {
                              if (_errs23) {
                                vErrors.length = _errs23;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs22 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.request_sha256 !== void 0) {
                            let data9 = data.request_sha256;
                            const _errs28 = errors;
                            if (errors === _errs28) {
                              if (typeof data9 === "string") {
                                if (!pattern9.test(data9)) {
                                  validate43.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate43.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs28 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.revision !== void 0) {
                              let data10 = data.revision;
                              const _errs30 = errors;
                              if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                                validate43.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs30) {
                                if (typeof data10 == "number" && isFinite(data10)) {
                                  if (data10 > 9007199254740991 || isNaN(data10)) {
                                    validate43.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                    return false;
                                  } else {
                                    if (data10 < 0 || isNaN(data10)) {
                                      validate43.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                      return false;
                                    }
                                  }
                                }
                              }
                              var valid0 = _errs30 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.run_id !== void 0) {
                                let data11 = data.run_id;
                                const _errs32 = errors;
                                const _errs33 = errors;
                                let valid5 = false;
                                const _errs34 = errors;
                                if (errors === _errs34) {
                                  if (typeof data11 === "string") {
                                    if (func1(data11) > 128) {
                                      const err8 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err8];
                                      } else {
                                        vErrors.push(err8);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data11) < 1) {
                                        const err9 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err9];
                                        } else {
                                          vErrors.push(err9);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern4.test(data11)) {
                                          const err10 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                          if (vErrors === null) {
                                            vErrors = [err10];
                                          } else {
                                            vErrors.push(err10);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  } else {
                                    const err11 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                  }
                                }
                                var _valid2 = _errs34 === errors;
                                valid5 = valid5 || _valid2;
                                const _errs36 = errors;
                                if (data11 !== null) {
                                  const err12 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                  if (vErrors === null) {
                                    vErrors = [err12];
                                  } else {
                                    vErrors.push(err12);
                                  }
                                  errors++;
                                }
                                var _valid2 = _errs36 === errors;
                                valid5 = valid5 || _valid2;
                                if (!valid5) {
                                  const err13 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                  if (vErrors === null) {
                                    vErrors = [err13];
                                  } else {
                                    vErrors.push(err13);
                                  }
                                  errors++;
                                  validate43.errors = vErrors;
                                  return false;
                                } else {
                                  errors = _errs33;
                                  if (vErrors !== null) {
                                    if (_errs33) {
                                      vErrors.length = _errs33;
                                    } else {
                                      vErrors = null;
                                    }
                                  }
                                }
                                var valid0 = _errs32 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.updated_at !== void 0) {
                                  let data12 = data.updated_at;
                                  const _errs38 = errors;
                                  if (errors === _errs38) {
                                    if (errors === _errs38) {
                                      if (typeof data12 === "string") {
                                        if (!formats0.validate(data12)) {
                                          validate43.errors = [{ instancePath: instancePath + "/updated_at", schemaPath: "#/properties/updated_at/format", keyword: "format", params: { format: "date-time" }, message: 'must match format "date-time"' }];
                                          return false;
                                        }
                                      } else {
                                        validate43.errors = [{ instancePath: instancePath + "/updated_at", schemaPath: "#/properties/updated_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                  }
                                  var valid0 = _errs38 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.wire_version !== void 0) {
                                    let data13 = data.wire_version;
                                    const _errs40 = errors;
                                    if (typeof data13 !== "string") {
                                      validate43.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                    if ("1" !== data13) {
                                      validate43.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                      return false;
                                    }
                                    var valid0 = _errs40 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.workers !== void 0) {
                                      let data14 = data.workers;
                                      const _errs42 = errors;
                                      const _errs43 = errors;
                                      if (errors === _errs43) {
                                        if (data14 && typeof data14 == "object" && !Array.isArray(data14)) {
                                          let missing2;
                                          if (data14.expected === void 0 && (missing2 = "expected") || data14.ready === void 0 && (missing2 = "ready")) {
                                            validate43.errors = [{ instancePath: instancePath + "/workers", schemaPath: "#/$defs/WorkerReadiness/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                            return false;
                                          } else {
                                            const _errs45 = errors;
                                            for (const key2 in data14) {
                                              if (!(key2 === "expected" || key2 === "ready")) {
                                                validate43.errors = [{ instancePath: instancePath + "/workers", schemaPath: "#/$defs/WorkerReadiness/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                                return false;
                                                break;
                                              }
                                            }
                                            if (_errs45 === errors) {
                                              if (data14.expected !== void 0) {
                                                let data15 = data14.expected;
                                                const _errs46 = errors;
                                                if (!(typeof data15 == "number" && (!(data15 % 1) && !isNaN(data15)) && isFinite(data15))) {
                                                  validate43.errors = [{ instancePath: instancePath + "/workers/expected", schemaPath: "#/$defs/WorkerReadiness/properties/expected/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                  return false;
                                                }
                                                if (errors === _errs46) {
                                                  if (typeof data15 == "number" && isFinite(data15)) {
                                                    if (data15 > 64 || isNaN(data15)) {
                                                      validate43.errors = [{ instancePath: instancePath + "/workers/expected", schemaPath: "#/$defs/WorkerReadiness/properties/expected/maximum", keyword: "maximum", params: { comparison: "<=", limit: 64 }, message: "must be <= 64" }];
                                                      return false;
                                                    } else {
                                                      if (data15 < 0 || isNaN(data15)) {
                                                        validate43.errors = [{ instancePath: instancePath + "/workers/expected", schemaPath: "#/$defs/WorkerReadiness/properties/expected/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                        return false;
                                                      }
                                                    }
                                                  }
                                                }
                                                var valid7 = _errs46 === errors;
                                              } else {
                                                var valid7 = true;
                                              }
                                              if (valid7) {
                                                if (data14.ready !== void 0) {
                                                  let data16 = data14.ready;
                                                  const _errs48 = errors;
                                                  if (!(typeof data16 == "number" && (!(data16 % 1) && !isNaN(data16)) && isFinite(data16))) {
                                                    validate43.errors = [{ instancePath: instancePath + "/workers/ready", schemaPath: "#/$defs/WorkerReadiness/properties/ready/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                    return false;
                                                  }
                                                  if (errors === _errs48) {
                                                    if (typeof data16 == "number" && isFinite(data16)) {
                                                      if (data16 > 64 || isNaN(data16)) {
                                                        validate43.errors = [{ instancePath: instancePath + "/workers/ready", schemaPath: "#/$defs/WorkerReadiness/properties/ready/maximum", keyword: "maximum", params: { comparison: "<=", limit: 64 }, message: "must be <= 64" }];
                                                        return false;
                                                      } else {
                                                        if (data16 < 0 || isNaN(data16)) {
                                                          validate43.errors = [{ instancePath: instancePath + "/workers/ready", schemaPath: "#/$defs/WorkerReadiness/properties/ready/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                          return false;
                                                        }
                                                      }
                                                    }
                                                  }
                                                  var valid7 = _errs48 === errors;
                                                } else {
                                                  var valid7 = true;
                                                }
                                              }
                                            }
                                          }
                                        } else {
                                          validate43.errors = [{ instancePath: instancePath + "/workers", schemaPath: "#/$defs/WorkerReadiness/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                          return false;
                                        }
                                      }
                                      var valid0 = _errs42 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate43.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate43.errors = vErrors;
      return errors === 0;
    }
    validate43.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.catalog = validate59;
    var pattern49 = new RegExp("^[0-9]+\\.[0-9]+\\.[0-9]+$", "u");
    function validate60(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate60.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.reference === void 0 && (missing0 = "reference") || data.scope === void 0 && (missing0 = "scope") || data.title === void 0 && (missing0 = "title") || data.tools === void 0 && (missing0 = "tools") || data.maximum_invocations === void 0 && (missing0 = "maximum_invocations") || data.maximum_deadline_seconds === void 0 && (missing0 = "maximum_deadline_seconds")) {
            validate60.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "maximum_deadline_seconds" || key0 === "maximum_invocations" || key0 === "reference" || key0 === "scope" || key0 === "title" || key0 === "tools")) {
                validate60.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.maximum_deadline_seconds !== void 0) {
                let data0 = data.maximum_deadline_seconds;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate60.errors = [{ instancePath: instancePath + "/maximum_deadline_seconds", schemaPath: "#/properties/maximum_deadline_seconds/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 86400 || isNaN(data0)) {
                      validate60.errors = [{ instancePath: instancePath + "/maximum_deadline_seconds", schemaPath: "#/properties/maximum_deadline_seconds/maximum", keyword: "maximum", params: { comparison: "<=", limit: 86400 }, message: "must be <= 86400" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate60.errors = [{ instancePath: instancePath + "/maximum_deadline_seconds", schemaPath: "#/properties/maximum_deadline_seconds/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                        return false;
                      }
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.maximum_invocations !== void 0) {
                  let data1 = data.maximum_invocations;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate60.errors = [{ instancePath: instancePath + "/maximum_invocations", schemaPath: "#/properties/maximum_invocations/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 1e5 || isNaN(data1)) {
                        validate60.errors = [{ instancePath: instancePath + "/maximum_invocations", schemaPath: "#/properties/maximum_invocations/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate60.errors = [{ instancePath: instancePath + "/maximum_invocations", schemaPath: "#/properties/maximum_invocations/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.reference !== void 0) {
                    let data2 = data.reference;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.profile_id === void 0 && (missing1 = "profile_id") || data2.version === void 0 && (missing1 = "version") || data2.sha256 === void 0 && (missing1 = "sha256")) {
                          validate60.errors = [{ instancePath: instancePath + "/reference", schemaPath: "#/$defs/LaunchProfileRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "profile_id" || key1 === "sha256" || key1 === "version")) {
                              validate60.errors = [{ instancePath: instancePath + "/reference", schemaPath: "#/$defs/LaunchProfileRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.profile_id !== void 0) {
                              let data3 = data2.profile_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate60.errors = [{ instancePath: instancePath + "/reference/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate60.errors = [{ instancePath: instancePath + "/reference/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate60.errors = [{ instancePath: instancePath + "/reference/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate60.errors = [{ instancePath: instancePath + "/reference/profile_id", schemaPath: "#/$defs/LaunchProfileRef/properties/profile_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.sha256 !== void 0) {
                                let data4 = data2.sha256;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (!pattern9.test(data4)) {
                                      validate60.errors = [{ instancePath: instancePath + "/reference/sha256", schemaPath: "#/$defs/LaunchProfileRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate60.errors = [{ instancePath: instancePath + "/reference/sha256", schemaPath: "#/$defs/LaunchProfileRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data2.version !== void 0) {
                                  let data5 = data2.version;
                                  const _errs14 = errors;
                                  if (typeof data5 !== "string") {
                                    validate60.errors = [{ instancePath: instancePath + "/reference/version", schemaPath: "#/$defs/LaunchProfileRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate60.errors = [{ instancePath: instancePath + "/reference/version", schemaPath: "#/$defs/LaunchProfileRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate60.errors = [{ instancePath: instancePath + "/reference", schemaPath: "#/$defs/LaunchProfileRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scope !== void 0) {
                      let data6 = data.scope;
                      const _errs16 = errors;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                          let missing2;
                          if (data6.tenant_id === void 0 && (missing2 = "tenant_id") || data6.project_id === void 0 && (missing2 = "project_id")) {
                            validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs19 === errors) {
                              if (data6.project_id !== void 0) {
                                let data7 = data6.project_id;
                                const _errs20 = errors;
                                if (errors === _errs20) {
                                  if (typeof data7 === "string") {
                                    if (func1(data7) > 128) {
                                      validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid4 = _errs20 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data6.tenant_id !== void 0) {
                                  let data8 = data6.tenant_id;
                                  const _errs22 = errors;
                                  if (errors === _errs22) {
                                    if (typeof data8 === "string") {
                                      if (func1(data8) > 128) {
                                        validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.title !== void 0) {
                        let data9 = data.title;
                        const _errs24 = errors;
                        if (errors === _errs24) {
                          if (typeof data9 === "string") {
                            if (func1(data9) > 160) {
                              validate60.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/maxLength", keyword: "maxLength", params: { limit: 160 }, message: "must NOT have more than 160 characters" }];
                              return false;
                            } else {
                              if (func1(data9) < 1) {
                                validate60.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              }
                            }
                          } else {
                            validate60.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.tools !== void 0) {
                          let data10 = data.tools;
                          const _errs26 = errors;
                          if (errors === _errs26) {
                            if (Array.isArray(data10)) {
                              if (data10.length > 64) {
                                validate60.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                                return false;
                              } else {
                                if (data10.length < 1) {
                                  validate60.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                                  return false;
                                } else {
                                  var valid5 = true;
                                  const len0 = data10.length;
                                  for (let i0 = 0; i0 < len0; i0++) {
                                    let data11 = data10[i0];
                                    const _errs28 = errors;
                                    const _errs29 = errors;
                                    if (errors === _errs29) {
                                      if (data11 && typeof data11 == "object" && !Array.isArray(data11)) {
                                        let missing3;
                                        if (data11.capability_id === void 0 && (missing3 = "capability_id") || data11.release === void 0 && (missing3 = "release") || data11.image_sha256 === void 0 && (missing3 = "image_sha256") || data11.contract_version === void 0 && (missing3 = "contract_version")) {
                                          validate60.errors = [{ instancePath: instancePath + "/tools/" + i0, schemaPath: "#/$defs/ToolBinding/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                          return false;
                                        } else {
                                          const _errs31 = errors;
                                          for (const key3 in data11) {
                                            if (!(key3 === "capability_id" || key3 === "contract_version" || key3 === "image_sha256" || key3 === "release")) {
                                              validate60.errors = [{ instancePath: instancePath + "/tools/" + i0, schemaPath: "#/$defs/ToolBinding/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                              return false;
                                              break;
                                            }
                                          }
                                          if (_errs31 === errors) {
                                            if (data11.capability_id !== void 0) {
                                              let data12 = data11.capability_id;
                                              const _errs32 = errors;
                                              if (errors === _errs32) {
                                                if (typeof data12 === "string") {
                                                  if (func1(data12) > 128) {
                                                    validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                    return false;
                                                  } else {
                                                    if (func1(data12) < 1) {
                                                      validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                      return false;
                                                    } else {
                                                      if (!pattern4.test(data12)) {
                                                        validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                        return false;
                                                      }
                                                    }
                                                  }
                                                } else {
                                                  validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                              }
                                              var valid7 = _errs32 === errors;
                                            } else {
                                              var valid7 = true;
                                            }
                                            if (valid7) {
                                              if (data11.contract_version !== void 0) {
                                                let data13 = data11.contract_version;
                                                const _errs34 = errors;
                                                if (typeof data13 !== "string") {
                                                  validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                                if ("1" !== data13) {
                                                  validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                                  return false;
                                                }
                                                var valid7 = _errs34 === errors;
                                              } else {
                                                var valid7 = true;
                                              }
                                              if (valid7) {
                                                if (data11.image_sha256 !== void 0) {
                                                  let data14 = data11.image_sha256;
                                                  const _errs36 = errors;
                                                  if (errors === _errs36) {
                                                    if (typeof data14 === "string") {
                                                      if (!pattern9.test(data14)) {
                                                        validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                        return false;
                                                      }
                                                    } else {
                                                      validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                      return false;
                                                    }
                                                  }
                                                  var valid7 = _errs36 === errors;
                                                } else {
                                                  var valid7 = true;
                                                }
                                                if (valid7) {
                                                  if (data11.release !== void 0) {
                                                    let data15 = data11.release;
                                                    const _errs38 = errors;
                                                    if (errors === _errs38) {
                                                      if (typeof data15 === "string") {
                                                        if (!pattern49.test(data15)) {
                                                          validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/release", schemaPath: "#/$defs/ToolBinding/properties/release/pattern", keyword: "pattern", params: { pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }, message: 'must match pattern "^[0-9]+\\.[0-9]+\\.[0-9]+$"' }];
                                                          return false;
                                                        }
                                                      } else {
                                                        validate60.errors = [{ instancePath: instancePath + "/tools/" + i0 + "/release", schemaPath: "#/$defs/ToolBinding/properties/release/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                        return false;
                                                      }
                                                    }
                                                    var valid7 = _errs38 === errors;
                                                  } else {
                                                    var valid7 = true;
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      } else {
                                        validate60.errors = [{ instancePath: instancePath + "/tools/" + i0, schemaPath: "#/$defs/ToolBinding/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                        return false;
                                      }
                                    }
                                    var valid5 = _errs28 === errors;
                                    if (!valid5) {
                                      break;
                                    }
                                  }
                                }
                              }
                            } else {
                              validate60.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs26 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate60.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate60.errors = vErrors;
      return errors === 0;
    }
    validate60.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate59(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate59.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.profiles === void 0 && (missing0 = "profiles")) {
            validate59.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "profiles" || key0 === "scope" || key0 === "wire_version")) {
                validate59.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.profiles !== void 0) {
                let data0 = data.profiles;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 32) {
                      validate59.errors = [{ instancePath: instancePath + "/profiles", schemaPath: "#/properties/profiles/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate60(data0[i0], { instancePath: instancePath + "/profiles/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate59.errors = [{ instancePath: instancePath + "/profiles", schemaPath: "#/properties/profiles/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data2 = data.scope;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  if (errors === _errs6) {
                    if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                      let missing1;
                      if (data2.tenant_id === void 0 && (missing1 = "tenant_id") || data2.project_id === void 0 && (missing1 = "project_id")) {
                        validate59.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs8 = errors;
                        for (const key1 in data2) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate59.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs8 === errors) {
                          if (data2.project_id !== void 0) {
                            let data3 = data2.project_id;
                            const _errs9 = errors;
                            if (errors === _errs9) {
                              if (typeof data3 === "string") {
                                if (func1(data3) > 128) {
                                  validate59.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data3) < 1) {
                                    validate59.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data3)) {
                                      validate59.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate59.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid3 = _errs9 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data2.tenant_id !== void 0) {
                              let data4 = data2.tenant_id;
                              const _errs11 = errors;
                              if (errors === _errs11) {
                                if (typeof data4 === "string") {
                                  if (func1(data4) > 128) {
                                    validate59.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data4) < 1) {
                                      validate59.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data4)) {
                                        validate59.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate59.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate59.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.wire_version !== void 0) {
                    let data5 = data.wire_version;
                    const _errs13 = errors;
                    if (typeof data5 !== "string") {
                      validate59.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("1" !== data5) {
                      validate59.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate59.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate59.errors = vErrors;
      return errors === 0;
    }
    validate59.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
