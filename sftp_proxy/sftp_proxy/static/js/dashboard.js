/**
 * Created by Xiaxi Li on 08/Jun/2015.
 */

$(document).ready(function() {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    var host1_table;

    $("#host1-table-div").on('click', 'tbody>tr', function () {
        $(this).toggleClass('selected');
    });

    $("#host2-table-div").on('click', 'tbody>tr', function () {
        $(this).toggleClass('selected');
    });

    $(".host1-form").submit(function(event) {
        event.preventDefault();
        var user_name = $("#host1-username").val();
        var password = $("#host1-password").val();
        var otc = $("#host1-otc").val();
        var csrftoken = getCookie('csrftoken');

        $.ajax({
                type: "POST",
                url: "/sftp_proxy/dashboard/login",
                data: {"username": user_name, "password": password, "otc": otc, "source": "host1"},
                success: function(returnedData) {
                    $("#host1-path").append('<a class="host1-path-link" href="/sftp_proxy/dashboard/list?path=/&source=host1">/</a>');
                    $("#host1-table-div").html('<table id="host1-table" class="table table-striped"></table>');
                    host1_table = $("#host1-table").dataTable({
                        "pagingType": "simple",
                        "dom": "tlp",
                        "language": {
                            "paginate": {
                                "next": "&gt;",
                                "previous": "&lt;"
                            }
                        },
                        "info": false,
                        "searching": false,
                        "lengthMenu": [[10, 25, 40, -1], [10, 25, 40, "All"]],
                        "data": returnedData["data"],
                        "columns": [{
                            "title": "Name",
                            "render": function(data, type, full, meta) {
                                var isFoler = full[2];
                                if (isFoler == "folder") {
                                    return '<i class="fa fa-folder-o"></i> <a class="host1-folder-link" href="/sftp_proxy/dashboard/list?path=/' + data + '&source=host1"> ' + data + '</a>';
                                } else {
                                    return '<i class="fa fa-file-o"></i> ' + data;
                                }
                            }
                        }, {
                            "title": "Size"
                        }, {
                            "visible": false
                        }]
                    });
                },
                dataType: "json",
                contentType: 'application/x-www-form-urlencoded; charset=utf-8',
                beforeSend: function(xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
    });

    $(document).on('click', '.host1-folder-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');
        var folder_name = $(this).text();
        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $("#host1-path").append('<a class="host1-path-link" href="/sftp_proxy/dashboard/list?path=' + path + '&source=host1">' + folder_name + '/</a>');
                reloadHost1TableData(returnedData["data"], path);
            }
        });
    });

    $(document).on('click', '.host1-path-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');

        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $(".host1-path-link").each(function(){
                    if (extractPath($(this).attr('href')).length > path.length) {
                        $(this).remove();
                    }
                });
                reloadHost1TableData(returnedData["data"], path);
            }
        });
    });

    function reloadHost1TableData(updatedData, path) {
        host1_table.api().destroy();
        $("#host1-table").empty();
        $("#host1-table-div").html('<table id="host1-table" class="table table-striped"></table>');
        var settings = {
            "pagingType": "simple",
            "dom": "tlp",
            "language": {
                "paginate": {
                    "next": "&gt;",
                    "previous": "&lt;"
                }
            },
            "info": false,
            "searching": false,
            "lengthMenu": [[10, 25, 40, -1], [10, 25, 40, "All"]],
            "data": updatedData,
            "columns": [{
                "title": "Name",
                "render": function (data, type, full, meta) {
                    var isFoler = full[2];
                    if (isFoler == "folder") {
                        if (path == "/") {
                            return '<i class="fa fa-folder-o"></i> <a class="host1-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + data + '&source=host1">' + data + '</a>';
                        } else {
                            return '<i class="fa fa-folder-o"></i> <a class="host1-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + '/' + data + '&source=host1">' + data + '</a>';
                        }
                    } else {
                        return '<i class="fa fa-file-o"></i> ' + data;
                    }
                }
            }, {
                "title": "Size"
            }, {
                "visible": false
            }]
        };
        host1_table = $("#host1-table").dataTable(settings);
    }

    var host2_table;
    $(".host2-form").submit(function(event) {
        event.preventDefault();
        var user_name = $("#host2-username").val();
        var password = $("#host2-password").val();
        var otc = $("#host2-otc").val();
        var csrftoken = getCookie('csrftoken');

        $.ajax({
                type: "POST",
                url: "/sftp_proxy/dashboard/login",
                data: {"username": user_name, "password": password, "otc": otc, "source": "host2"},
                success: function(returnedData) {
                    $("#host2-path").append('<a class="host2-path-link" href="/sftp_proxy/dashboard/list?path=/&source=host2">/</a>');
                    $("#host2-table-div").html('<table id="host2-table" class="table table-striped"></table>');
                    host2_table = $("#host2-table").dataTable({
                        "pagingType": "simple",
                        "dom": "tlp",
                        "language": {
                            "paginate": {
                                "next": "&gt;",
                                "previous": "&lt;"
                            }
                        },
                        "info": false,
                        "searching": false,
                        "lengthMenu": [[10, 25, 40, -1], [10, 25, 40, "All"]],
                        "data": returnedData["data"],
                        "columns": [{
                            "title": "Name",
                            "render": function(data, type, full, meta) {
                                var isFoler = full[2];
                                if (isFoler == "folder") {
                                    return '<i class="fa fa-folder-o"></i> <a class="host2-folder-link" href="/sftp_proxy/dashboard/list?path=/' + data + '&source=host2"> ' + data + '</a>';
                                } else {
                                    return '<i class="fa fa-file-o"></i> ' + data;
                                }
                            }
                        }, {
                            "title": "Size"
                        }, {
                            "visible": false
                        }]
                    });
                },
                dataType: "json",
                contentType: 'application/x-www-form-urlencoded; charset=utf-8',
                beforeSend: function(xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
    });

    $(document).on('click', '.host2-folder-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');
        var folder_name = $(this).text();
        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $("#host2-path").append('<a class="host2-path-link" href="/sftp_proxy/dashboard/list?path=' + path + '&source=host2">' + folder_name + '/</a>');
                reloadHost2TableData(returnedData["data"], path);
            }
        });
    });

    $(document).on('click', '.host2-path-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');

        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $(".host2-path-link").each(function(){
                    if (extractPath($(this).attr('href')).length > path.length) {
                        $(this).remove();
                    }
                });
                reloadHost2TableData(returnedData["data"], path);
            }
        });
    });

    function reloadHost2TableData(updatedData, path) {
        host2_table.api().destroy();
        $("#host2-table").empty();
        $("#host2-table-div").html('<table id="host2-table" class="table table-striped"></table>');
        var settings = {
            "pagingType": "simple",
            "dom": "tlp",
            "language": {
                "paginate": {
                    "next": "&gt;",
                    "previous": "&lt;"
                }
            },
            "info": false,
            "searching": false,
            "lengthMenu": [[10, 25, 40, -1], [10, 25, 40, "All"]],
            "data": updatedData,
            "columns": [{
                "title": "Name",
                "render": function (data, type, full, meta) {
                    var isFoler = full[2];
                    if (isFoler == "folder") {
                        if (path == "/") {
                            return '<i class="fa fa-folder-o"></i> <a class="host2-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + data + '&source=host2">' + data + '</a>';
                        } else {
                            return '<i class="fa fa-folder-o"></i> <a class="host2-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + '/' + data + '&source=host2">' + data + '</a>';
                        }
                    } else {
                        return '<i class="fa fa-file-o"></i> ' + data;
                    }
                }
            }, {
                "title": "Size"
            }, {
                "visible": false
            }]
        };
        host2_table = $("#host2-table").dataTable(settings);
    }

    $('#host2-transfer-btn').click(function() {
        var transferredData = [];

        host2_table.api().rows('.selected').data().each(function(item) {
            transferredData.push({"name": item[0], "type": item[2]});
        });

        var from_path = extractPath($('.host2-path-link:last').attr('href'));
        var to_path = extractPath($('.host1-path-link:last').attr('href'));
        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/transfer",
            data: JSON.stringify({"from": {"path": from_path, "name": "host2", "data": transferredData}, "to": {"path": to_path, "name": "host1"}}),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function(returnedData) {
                var url = "/sftp_proxy/dashboard/list?path=" + to_path + "&source=host1";
                $.ajax({
                    type: "GET",
                    url: url,
                    success: function(updatedData) {
                        reloadHost1TableData(updatedData["data"], updatedData["path"]);
                    }
                });
            }
        });
    });

    $('#host2-delete-btn').click(function() {
        var transferredData = [];

        host2_table.api().rows('.selected').data().each(function(item) {
            transferredData.push({"name": item[0], "type": item[2]});
        });

        var path = extractPath($('.host2-path-link:last').attr('href'));
        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/delete",
            data: JSON.stringify({"source": "host2", "path": path, "data": transferredData}),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function(returnedData) {
                var url = "/sftp_proxy/dashboard/list?path=" + path + "&source=host2";
                $.ajax({
                    type: "GET",
                    url: url,
                    success: function(updatedData) {
                        reloadHost2TableData(updatedData["data"], updatedData["path"]);
                    }
                });
            }
        });
    });

    $('#host1-transfer-btn').click(function() {
        var transferredData = [];

        host1_table.api().rows('.selected').data().each(function(item) {
            transferredData.push({"name": item[0], "type": item[2]});
        });

        var from_path = extractPath($('.host1-path-link:last').attr('href'));
        var to_path = extractPath($('.host2-path-link:last').attr('href'));
        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/transfer",
            data: JSON.stringify({"from": {"path": from_path, "name": "host1", "data": transferredData}, "to": {"path": to_path, "name": "host2"}}),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function() {
                var url = "/sftp_proxy/dashboard/list?path=" + to_path + "&source=host2";
                $.ajax({
                    type: "GET",
                    url: url,
                    success: function(updatedData) {
                        reloadHost2TableData(updatedData["data"], updatedData["path"]);
                    }
                });
            }
        });
    });

    $('#host1-delete-btn').click(function() {
        var transferredData = [];

        host1_table.api().rows('.selected').data().each(function(item) {
            transferredData.push({"name": item[0], "type": item[2]});
        });

        var path = extractPath($('.host1-path-link:last').attr('href'));
        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/delete",
            data: JSON.stringify({"source": "host1", "path": path, "data": transferredData}),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function(returnedData) {
                var url = "/sftp_proxy/dashboard/list?path=" + path + "&source=host1";
                $.ajax({
                    type: "GET",
                    url: url,
                    success: function(updatedData) {
                        reloadHost1TableData(updatedData["data"], updatedData["path"]);
                    }
                });
            }
        });
    });

    function extractPath(href) {
        var path = href.substring(href.indexOf("?") + 1, href.indexOf("&"));
        return path.substring(path.indexOf("=") + 1);
    }
});
