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


    var tsd_table;

    $("#tsd-table-div").on('click', 'tbody>tr', function () {
        if ($(this).find('.tsd-folder-link').length == 0) {
            $(this).toggleClass('selected');
        }
    });

    $("#mosler-table-div").on('click', 'tbody>tr', function () {
        if ($(this).find('.mosler-folder-link').length == 0) {
            $(this).toggleClass('selected');
        }
    });

    $(".tsd-form").submit(function(event) {
        event.preventDefault();
        var user_name = $("#tsd-username").val();
        var password = $("#tsd-password").val();
        var otc = $("#tsd-otc").val();
        var csrftoken = getCookie('csrftoken');

        $.ajax({
                type: "POST",
                url: "/sftp_proxy/dashboard/login",
                data: {"username": user_name, "password": password, "otc": otc, "source": "tsd"},
                success: function(returnedData) {
                    $("#tsd-path").append('<a class="tsd-path-link" href="/sftp_proxy/dashboard/list?path=/&source=tsd">/</a>');
                    $("#tsd-table-div").html('<table id="tsd-table" class="table table-striped"></table>');
                    tsd_table = $("#tsd-table").dataTable({
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
                                    return '<i class="fa fa-folder-o"></i> <a class="tsd-folder-link" href="/sftp_proxy/dashboard/list?path=/' + data + '&source=tsd"> ' + data + '</a>';
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

    $(document).on('click', '.tsd-folder-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');
        var folder_name = $(this).text();
        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $("#tsd-path").append('<a class="tsd-path-link" href="/sftp_proxy/dashboard/list?path=' + path + '&source=tsd">' + folder_name + '/</a>');
                reloadTsdTableData(returnedData["data"], path);
            }
        });
    });

    $(document).on('click', '.tsd-path-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');

        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $(".tsd-path-link").each(function(){
                    if (extractPath($(this).attr('href')).length > path.length) {
                        $(this).remove();
                    }
                });
                reloadTsdTableData(returnedData["data"], path);
            }
        });
    });

    function reloadTsdTableData(updatedData, path) {
        tsd_table.api().destroy();
        $("#tsd-table").empty();
        $("#tsd-table-div").html('<table id="tsd-table" class="table table-striped"></table>');
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
                        return '<i class="fa fa-folder-o"></i> <a class="tsd-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + '/' + data + '&source=tsd">' + data + '</a>';
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
        tsd_table = $("#tsd-table").dataTable(settings);
    }

    var mosler_table;
    $(".mosler-form").submit(function(event) {
        event.preventDefault();
        var user_name = $("#mosler-username").val();
        var password = $("#mosler-password").val();
        var otc = $("#mosler-otc").val();
        var csrftoken = getCookie('csrftoken');

        $.ajax({
                type: "POST",
                url: "/sftp_proxy/dashboard/login",
                data: {"username": user_name, "password": password, "otc": otc, "source": "mosler"},
                success: function(returnedData) {
                    $("#mosler-path").append('<a class="mosler-path-link" href="/sftp_proxy/dashboard/list?path=/&source=mosler">/</a>');
                    $("#mosler-table-div").html('<table id="mosler-table" class="table table-striped"></table>');
                    mosler_table = $("#mosler-table").dataTable({
                        "data": returnedData["data"],
                        "columns": [{
                            "title": "Name",
                            "render": function(data, type, full, meta) {
                                var isFoler = full[2];
                                if (isFoler == "folder") {
                                    return '<i class="fa fa-folder-o"></i> <a class="mosler-folder-link" href="/sftp_proxy/dashboard/list?path=/' + data + '&source=mosler"> ' + data + '</a>';
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

    $(document).on('click', '.mosler-folder-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');
        var folder_name = $(this).text();
        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $("#mosler-path").append('<a class="mosler-path-link" href="/sftp_proxy/dashboard/list?path=' + path + '&source=mosler">' + folder_name + '/</a>');
                reloadMoslerTableData(returnedData["data"], path);
            }
        });
    });

    $(document).on('click', '.mosler-path-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');

        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                var path = returnedData["path"];
                $(".mosler-path-link").each(function(){
                    if (extractPath($(this).attr('href')).length > path.length) {
                        $(this).remove();
                    }
                });
                reloadMoslerTableData(returnedData["data"], path);
            }
        });
    });

    function reloadMoslerTableData(updatedData, path) {
        mosler_table.api().destroy();
        $("#mosler-table").empty();
        $("#mosler-table-div").html('<table id="mosler-table" class="table table-striped"></table>');
        var settings = {
            "data": updatedData,
            "columns": [{
                "title": "Name",
                "render": function (data, type, full, meta) {
                    var isFoler = full[2];
                    if (isFoler == "folder") {
                        return '<i class="fa fa-folder-o"></i> <a class="mosler-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + '/' + data + '&source=mosler">' + data + '</a>';
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
        mosler_table = $("#mosler-table").dataTable(settings);
    }

    $('#mosler-transfer-btn').click(function() {
        var transferredData = [];

        mosler_table.api().rows('.selected').data().each(function(item) {
            transferredData.push({"name": item[0], "type": item[2]});
        });

        var from_path = extractPath($('.mosler-path-link:last').attr('href'));
        var to_path = extractPath($('.tsd-path-link:last').attr('href'));
        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/transfer",
            data: JSON.stringify({"from": {"path": from_path, "name": "mosler", "data": transferredData}, "to": {"path": to_path, "name": "tsd"}}),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function(returnedData) {
                var url = "/sftp_proxy/dashboard/list?path=" + to_path + "&source=tsd";
                $.ajax({
                    type: "GET",
                    url: url,
                    success: function(updatedData) {
                        reloadTsdTableData(updatedData["data"], updatedData["path"]);
                    }
                });
            }
        });
    });

    $('#tsd-transfer-btn').click(function() {
        var transferredData = [];

        tsd_table.api().rows('.selected').data().each(function(item) {
            transferredData.push({"name": item[0], "type": item[2]});
        });

        var from_path = extractPath($('.tsd-path-link:last').attr('href'));
        var to_path = extractPath($('.mosler-path-link:last').attr('href'));
        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/transfer",
            data: JSON.stringify({"from": {"path": from_path, "name": "tsd", "data": transferredData}, "to": {"path": to_path, "name": "mosler"}}),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function() {
                var url = "/sftp_proxy/dashboard/list?path=" + to_path + "&source=mosler";
                $.ajax({
                    type: "GET",
                    url: url,
                    success: function(updatedData) {
                        reloadMoslerTableData(updatedData["data"], updatedData["path"]);
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