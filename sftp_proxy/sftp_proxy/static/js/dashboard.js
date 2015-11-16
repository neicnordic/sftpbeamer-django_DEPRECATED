/**
 * Created by Xiaxi Li on 08/Jun/2015.
 */

$(document).ready(function() {
    $("#host1-table-div").on('click', 'tbody>tr', function () {
        $(this).toggleClass('selected');
    });

    $("#host2-table-div").on('click', 'tbody>tr', function () {
        $(this).toggleClass('selected');
    });

    $(document).on('click', '.host1-folder-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');
        var folder_name = $(this).text();
        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                if (returnedData["error"]) {
                    change_modal_property("Error", returnedData["error"]);
                    var modal = $('#info_modal');
                    modal.one('hide.bs.modal', function (event) {
                        location.reload();
                    });
                    modal.modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else if (returnedData["exception"]) {
                    change_modal_property("Exception", returnedData["exception"]);
                    $('#info_modal').modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else {
                    var path = returnedData["path"];
                    $("#host1-path").append('<a class="host1-path-link" href="/sftp_proxy/dashboard/list?path=' + path + '&source=host1">' + folder_name + '/</a>');
                    reloadTableData(returnedData["data"], path, "host1");
                }
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
                if (returnedData["error"]) {
                    change_modal_property("Error", returnedData["error"]);
                    var modal = $('#info_modal');
                    modal.one('hide.bs.modal', function (event) {
                        location.reload();
                    });
                    modal.modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else if (returnedData["exception"]) {
                    change_modal_property("Exception", returnedData["exception"]);
                    $('#info_modal').modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else {
                    var path = returnedData["path"];
                    $(".host1-path-link").each(function () {
                        if (extractPath($(this).attr('href')).length > path.length) {
                            $(this).remove();
                        }
                    });
                    reloadTableData(returnedData["data"], path, "host1");
                }
            }
        });
    });

    function disconnect_sftp(source) {
        if (source == 'host1' || source == 'host2') {
            $.ajax({
                type: "GET",
                url: "/sftp_proxy/dashboard/disconnect?source=" + source,
                success: function () {
                    fetch_table(source).api().destroy();
                    $("#" + source + "-table").empty();
                    $("#" + source + "-table-div").html("");
                    $("#" + source + "-path").html("");
                    $("#" + source + "-delete-btn").prop("disabled", true);
                    $("#" + source + "-transfer-btn").prop("disabled", true);
                    $("#" + source + "-disconnect-btn").prop("disabled", true);
                    $("#" + source + "-submit-btn").prop("disabled", false);
                    $("#" + source + "-username").prop("disabled", false);
                    $("#" + source + "-hostname").prop("disabled", false);
                    $("#" + source + "-port").prop("disabled", false);
                }
            });
        }
    }

    $('#host1-disconnect-btn').click(function(event) {
        event.preventDefault();
        disconnect_sftp('host1');
    });

    $('#host2-disconnect-btn').click(function(event) {
        event.preventDefault();
        disconnect_sftp('host2');
    });

    $(document).on('click', '.host2-folder-link', function(event) {
        event.preventDefault();
        var href = $(this).attr('href');
        var folder_name = $(this).text();
        $.ajax({
            type: "GET",
            url: href,
            success: function(returnedData) {
                if (returnedData["error"]) {
                    change_modal_property("Error", returnedData["error"]);
                    var modal = $('#info_modal');
                    modal.one('hide.bs.modal', function (event) {
                        location.reload();
                    });
                    modal.modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else if (returnedData["exception"]) {
                    change_modal_property("Exception", returnedData["exception"]);
                    $('#info_modal').modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else {
                    var path = returnedData["path"];
                    $("#host2-path").append('<a class="host2-path-link" href="/sftp_proxy/dashboard/list?path=' + path + '&source=host2">' + folder_name + '/</a>');
                    reloadTableData(returnedData["data"], path, "host2");
                }
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
                if (returnedData["error"]) {
                    change_modal_property("Error", returnedData["error"]);
                    var modal = $('#info_modal');
                    modal.one('hide.bs.modal', function (event) {
                        location.reload();
                    });
                    modal.modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else if (returnedData["exception"]) {
                    change_modal_property("Exception", returnedData["exception"]);
                    $('#info_modal').modal({
                        keyboard: false,
                        backdrop: 'static'
                    });
                } else {
                    var path = returnedData["path"];
                    $(".host2-path-link").each(function () {
                        if (extractPath($(this).attr('href')).length > path.length) {
                            $(this).remove();
                        }
                    });
                    reloadTableData(returnedData["data"], path, "host2");
                }
            }
        });
    });

    $('#host2-transfer-btn').click(function() {
        var transferredData = [];

        var selected_items = host2_table.api().rows('.selected').data();
        if (selected_items.length == 0) {
            change_modal_property("Information", "No files or folders are selected.");
            $('#info_modal').modal({
                keyboard: false,
                backdrop: 'static'
            });
        } else {
            selected_items.each(function (item) {
                transferredData.push({"name": item[0], "type": item[2]});
            });

            var from_path = extractPath($('.host2-path-link:last').attr('href'));
            var to_path = extractPath($('.host1-path-link:last').attr('href'));
            var csrftoken = getCookie('csrftoken');

            $.ajax({
                type: "POST",
                url: "/sftp_proxy/dashboard/transfer",
                data: JSON.stringify({
                    "from": {"path": from_path, "name": "host2", "data": transferredData},
                    "to": {"path": to_path, "name": "host1"}
                }),
                dataType: "json",
                contentType: 'application/json; charset=utf-8',
                beforeSend: function (xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                },
                success: function (returnedData) {
                    if (returnedData["error"]) {
                        change_modal_property("Error", returnedData["error"]);
                        var modal = $('#info_modal');
                        modal.one('hide.bs.modal', function (event) {
                            location.reload();
                        });
                        modal.modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else if (returnedData["exception"]) {
                        change_modal_property("Exception", returnedData["exception"]);
                        $('#info_modal').modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else {
                        var session_key = returnedData["session_key"];
                        var ws = create_ws_connection();
                        ws.onopen = function () {
                            ws.send(JSON.stringify({
                                "session_key": session_key,
                                "from": {"path": from_path, "name": "host2", "data": transferredData},
                                "to": {"path": to_path, "name": "host1"}}));
                        };
                        ws.onmessage = function (event) {
                            if (event.data == "done") {
                                change_modal_property("Information", "File transfer is done.");
                                $('#info_modal').modal({
                                    keyboard: false,
                                    backdrop: 'static'
                                });
                                ws.close();
                            } else {
                                refresh_progress_bar(JSON.parse(event.data));
                            }
                        };
                    }
                }
            });
        }
    });

    $('#host2-delete-btn').click(function() {
        var transferredData = [];

        var selected_items = host2_table.api().rows('.selected').data();
        if (selected_items.length == 0) {
            change_modal_property("Information", "No files or folders are selected.");
            $('#info_modal').modal({
                keyboard: false,
                backdrop: 'static'
            });
        } else {
            selected_items.each(function (item) {
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
                beforeSend: function (xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                },
                success: function (returnedData) {
                    if (returnedData["error"]) {
                        change_modal_property("Error", returnedData["error"]);
                        var modal = $('#info_modal');
                        modal.one('hide.bs.modal', function (event) {
                            location.reload();
                        });
                        modal.modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else if (returnedData["exception"]) {
                        change_modal_property("Exception", returnedData["exception"]);
                        $('#info_modal').modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else {
                        var url = "/sftp_proxy/dashboard/list?path=" + path + "&source=host2";
                        $.ajax({
                            type: "GET",
                            url: url,
                            success: function (updatedData) {
                                reloadTableData(updatedData["data"], updatedData["path"], "host2");
                            }
                        });
                    }
                }
            });
        }
    });

    $('#host1-transfer-btn').click(function() {
        var transferredData = [];

        var selected_items = host1_table.api().rows('.selected').data();
        if (selected_items.length == 0) {
            change_modal_property("Information", "No files or folders are selected.");
            $('#info_modal').modal({
                keyboard: false,
                backdrop: 'static'
            });
        } else {
            selected_items.each(function (item) {
                transferredData.push({"name": item[0], "type": item[2]});
            });

            var from_path = extractPath($('.host1-path-link:last').attr('href'));
            var to_path = extractPath($('.host2-path-link:last').attr('href'));
            var csrftoken = getCookie('csrftoken');


            $.ajax({
                type: "POST",
                url: "/sftp_proxy/dashboard/transfer",
                data: JSON.stringify({
                    "from": {"path": from_path, "name": "host1", "data": transferredData},
                    "to": {"path": to_path, "name": "host2"}
                }),
                dataType: "json",
                contentType: 'application/json; charset=utf-8',
                beforeSend: function (xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                },
                success: function (returnedData) {
                    if (returnedData["error"]) {
                        change_modal_property("Error", returnedData["error"]);
                        var modal = $('#info_modal');
                        modal.one('hide.bs.modal', function (event) {
                            location.reload();
                        });
                        modal.modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else if (returnedData["exception"]) {
                        change_modal_property("Exception", returnedData["exception"]);
                        $('#info_modal').modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else {
                        var session_key = returnedData["session_key"];
                        var ws = create_ws_connection();
                        ws.onopen = function () {
                            ws.send(JSON.stringify({
                                "session_key": session_key,
                                "from": {"path": from_path, "name": "host1", "data": transferredData},
                                "to": {"path": to_path, "name": "host2"}}));
                        };
                        ws.onmessage = function (event) {
                            if (event.data == "done") {
                                change_modal_property("Information", "File transfer is done.");
                                $('#info_modal').modal({
                                    keyboard: false,
                                    backdrop: 'static'
                                });
                                ws.close();
                            } else {
                                refresh_progress_bar(JSON.parse(event.data));
                            }
                        };
                    }
                }
            });
        }
    });

    $('#host1-delete-btn').click(function() {
        var transferredData = [];

        var selected_items = host1_table.api().rows('.selected').data();
        if (selected_items.length == 0) {
            change_modal_property("Information", "No files or folders are selected.");
            $('#info_modal').modal({
                keyboard: false,
                backdrop: 'static'
            });
        } else {
            selected_items.each(function (item) {
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
                beforeSend: function (xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                },
                success: function (returnedData) {
                    if (returnedData["error"]) {
                        change_modal_property("Error", returnedData["error"]);
                        var modal = $('#info_modal');
                        modal.one('hide.bs.modal', function (event) {
                            location.reload();
                        });
                        modal.modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else if (returnedData["exception"]) {
                        change_modal_property("Exception", returnedData["exception"]);
                        $('#info_modal').modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else {
                        var url = "/sftp_proxy/dashboard/list?path=" + path + "&source=host1";
                        $.ajax({
                            type: "GET",
                            url: url,
                            success: function (updatedData) {
                                reloadTableData(updatedData["data"], updatedData["path"], "host1");
                            }
                        });
                    }
                }
            });
        }
    });

    function extractPath(href) {
        var path = href.substring(href.indexOf("?") + 1, href.indexOf("&"));
        return path.substring(path.indexOf("=") + 1);
    }

    function reloadTableData(updatedData, path, source) {
        fetch_table(source).api().destroy();
        $("#" + source + "-table").empty();
        $("#" + source + "-table-div").html('<table id="' + source + '-table" class="table table-striped"></table>');
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
                            return '<i class="fa fa-folder-o"></i> <a class="' + source + '-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + data + '&source=' + source + '">' + data + '</a>';
                        } else {
                            return '<i class="fa fa-folder-o"></i> <a class="' + source + '-folder-link" href="/sftp_proxy/dashboard/list?path=' + path + '/' + data + '&source=' + source + '">' + data + '</a>';
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
        set_table(source, $("#" + source + "-table").dataTable(settings));
    }
});
