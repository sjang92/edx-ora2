/**
 Interface for response (submission) view.

 Args:
 element (DOM element): The DOM element representing the XBlock.
 server (OpenAssessment.Server): The interface to the XBlock server.
 baseView (OpenAssessment.BaseView): Container view.

 Returns:
 OpenAssessment.ResponseView
 **/
OpenAssessment.GroupResponseView = function(element, server, baseView) {
    this.element = element;
    this.server = server;
    this.baseView = baseView;
};


OpenAssessment.GroupResponseView.prototype = {

    /**
     Load the response (submission) view.
     **/
    load: function() {
        var view = this;
        this.server.render('group_submission').done(
            function(html) {
                // Load the HTML and install event handlers
                $('#openassessment__group_response', view.element).replaceWith(html);
                view.installHandlers();
            }
        ).fail(function(errMsg) {
                view.baseView.showLoadError('group_response');
            });
    },

    /**
     Install event handlers for the view.
     **/
    installHandlers: function() {
        var sel = $('#openassessment__group_response', this.element);
        var view = this;

        // Install a click handler for collapse/expand
        this.baseView.setUpCollapseExpand(sel);

        // Install change handler for textarea (to enable submission button)
        var handleChange = function(eventData) { view.handleResponseChanged(); };
        sel.find('#submission__answer__value').on('change keyup drop paste', handleChange);

        // Install a click handler for submission
        sel.find('#step--response__submit').click(
            function(eventObject) {
                var sel = $(eventObject.target).closest('.wrapper--step__content');
                var sub_sel = $('#submission__answer__value', sel);
                var order_sel = $('#response__order_num', sel);
                var order = order_sel[0].innerText;
                var answer = sub_sel.val();
                // Override default form submission
                eventObject.preventDefault();
                view.submit(answer, order);
            }
        );
    },

    /**
     Enable/disable the submit button.
     Check that whether the submit button is enabled.

     Args:
     enabled (bool): If specified, set the state of the button.

     Returns:
     bool: Whether the button is enabled.

     Examples:
     >> view.submitEnabled(true);  // enable the button
     >> view.submitEnabled();  // check whether the button is enabled
     >> true
     **/
    submitEnabled: function(enabled) {
        var sel = $('#step--response__submit', this.element);
        if (typeof enabled === 'undefined') {
            return !sel.hasClass('is--disabled');
        } else {
            sel.toggleClass('is--disabled', !enabled);
        }
    },

    /**
     Set the response text.
     Retrieve the response text.

     Args:
     text (string): If specified, the text to set for the response.

     Returns:
     string: The current response text.
     **/
    response: function(text) {
        var sel = $('#submission__answer__value', this.element);
        if (typeof text === 'undefined') {
            return sel.val();
        } else {
            sel.val(text);
        }
    },

    /**
     Enable/disable the submission and save buttons based on whether
     the user has entered a response.
     **/
    handleResponseChanged: function() {
        // Enable the save/submit button only for non-blank responses
        var isBlank = ($.trim(this.response()) !== '');
        this.submitEnabled(isBlank);
    },

    /**
     Send a response submission to the server and update the view.
     **/
    submit: function(submission, order) {
        // Immediately disable the submit button to prevent multiple submission
        this.submitEnabled(false);

        var view = this;
        var baseView = this.baseView;

        this.confirmSubmission()
            // On confirmation, send the submission to the server
            // The callback returns a promise so we can attach
            // additional callbacks after the confirmation.
            // NOTE: in JQuery >=1.8, `pipe()` is deprecated in favor of `then()`,
            // but we're using JQuery 1.7 in the LMS, so for now we're stuck with `pipe()`.
            .pipe(function() {
                baseView.toggleActionError('response', null);

                // Send the submission to the server, returning the promise.
                return view.server.submitProjectPart(submission, order);
            })

            // If the submission was submitted successfully, move to the next step
            .done($.proxy(view.moveToNextStep, view))

            // Handle submission failure (either a server error or cancellation),
            .fail(function(errCode, errMsg) {
                // If the error is "multiple submissions", then we should move to the next
                // step.  Otherwise, the user will be stuck on the current step with no
                // way to continue.
                if (errCode == 'ENOMULTI') { view.moveToNextStep(); }
                else {
                    // If there is an error message, display it
                    if (errMsg) { baseView.toggleActionError('submit', errMsg); }

                    // Re-enable the submit button so the user can retry
                    view.submitEnabled(true);
                }
            });
    },

    /**
     Transition the user to the next step in the workflow.
     **/
    moveToNextStep: function() {
        this.load();
        this.baseView.loadAssessmentModules();
    },

    /**
     Make the user confirm before submitting a response.

     Returns:
     JQuery deferred object, which is:
     * resolved if the user confirms the submission
     * rejected if the user cancels the submission
     **/
    confirmSubmission: function() {
        var msg = (
            "You're about to submit your response for this assignment. " +
                "After you submit this response, you can't change it or submit a new response."
            );
        // TODO -- UI for confirmation dialog instead of JS confirm
        return $.Deferred(function(defer) {
            if (confirm(msg)) { defer.resolve(); }
            else { defer.reject(); }
        });
    }
};
