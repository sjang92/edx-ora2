/**
 Interface for student-facing views.

 Args:
 runtime (Runtime): an XBlock runtime instance.
 element (DOM element): The DOM element representing this XBlock.

 Returns:
 Group.BaseView
 **/

/* Namespace for Group */
if (typeof Group == "undefined" || !Group) {
    Group = {};
}


// Stub gettext if the runtime doesn't provide it
if (typeof window.gettext === 'undefined') {
    window.gettext = function(text) { return text; };
}

Group.BaseView = function(runtime, element) {
    this.runtime = runtime;
    this.element = element;
};


Group.BaseView.prototype = {

    /**
     Load base view for groups.
     **/
    load: function() {
        this.installHandlers();
    },

    /**
     Construct the URL for the handler, specific to one instance of the XBlock on the page.

     Args:
     handler (string): The name of the XBlock handler.

     Returns:
     URL (string)
     **/
    url: function(handler) {
        return this.runtime.handlerUrl(this.element, handler);
    },

    /**
     Install event handlers for the view.
     **/
    installHandlers: function() {
        var sel = $('#group__base', this.element);
        var view = this;
        // Install key handler for form
        sel.find('#join_group_form').submit(
            function(eventObject) {
                eventObject.preventDefault();
                view.joinGroup();
            }
        );

        // Install a click handler for joining a group.
        sel.find('#submit_join_group').click(
            function(eventObject) {
                eventObject.preventDefault();
                view.joinGroup();
            }
        );
    },

    /**
     Load the Student Info section in Staff Info.
     **/
    joinGroup: function() {
        var url = this.url('join_group');
        var sel = $('#group__base', this.element);
        var student_name = sel.find('#group__student_name').val();
        var student_email = sel.find('#group__student_email').val();
        return $.Deferred(function(defer) {
            $.ajax({
                url: url,
                type: "POST",
                dataType: "html",
                data: JSON.stringify({
                    student_name: student_name,
                    student_email: student_email
                })
            }).done(function(data) {
                    defer.resolveWith(this, [data]);
                }).fail(function(data) {
                    defer.rejectWith(this, [gettext('This section could not be loaded.')]);
                });
        }).promise();
    }

};

/* XBlock JavaScript entry point for GroupBlock. */
function GroupBlock(runtime, element) {
    /**
     Render views within the base view on page load.
     **/
    var view = new Group.BaseView(runtime, element);
    view.load();
}
