(function(window, $, config) {
    var config = formatObjJSNaming(config)

    $(document).ready(function() {

        function queryQrStatue(qrId, last) {
            $.ajax({
                type: 'GET',
                url: '/query/' + qrId + '/' + (last ? last + '/' : ''),
                dataType: 'script',
                cache: !1,
            }).then(
                function(data) {
                    console.log(data)
                    var errCode = window.wx_errcode
                    switch (errCode) {
                        case 405:
                            $('#login_url').html(login_url)
                            // window.location.href = login_url
                            break
                        case 404:
                            $('#wx_after_scan').show()
                            setTimeout(queryQrStatue, 100, qrId, errCode)
                            break
                        case 403:
                            $('#wx_after_cancel').show()
                            break
                        case 402:
                        case 500:
                            window.location.reload()
                            break;
                        case 408:
                            setTimeout(queryQrStatue, 2e3, qrId)
                    }
                },
                function() {

                }
            )
        }
        queryQrStatue(config.qrId)

    })
})(window, window.jQuery, window.config);


function formatStrJsNaming(str) {
    var doUpper = false, formatted = []
    for (var index in str) {
        var char = str[index]
        if (char === '_')
            doUpper = true
        else {
            formatted.push(doUpper === true ? char.toUpperCase() : char)
            doUpper = false
        }
    }
    return formatted.join('')
}

function formatObjJSNaming(data) {
    var formatted = null
    if (data instanceof Array) {
        formatted = []
        for (var index in data) {
            formatted.push(formatObjJSNaming(data[index]))
        }
    }
    else if(data instanceof Object) {
        formatted = {}
        for (var key in data) {
            formatted[formatStrJsNaming(key)] = formatObjJSNaming(data[key])
        }
    }
    else {
        formatted = data
    }
    return formatted
}
