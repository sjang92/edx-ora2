/**
 Interface for group assessment view

 **/
OpenAssessment.GroupView = function(element, server, baseView) {
    this.element = element;
    this.server = server;
    this.baseView = baseView;
    this.rubric = null;
};


OpenAssessment.GroupView.prototype = {

    /**
     Load the peer assessment view.
     **/
    load: function() {
        var view = this;
        this.server.render('group_assessment').done(
            function(html) {
                // Load the HTML and install event handlers
                $('#openassessment__group-assessment', view.element).replaceWith(html);
                view.installHandlers(false);
            }
        ).fail(function(errMsg) {
                view.baseView.showLoadError('group-assessment');
            });
    },

    /**
     Install event handlers for the view.

     Args:
     isContinuedAssessment (boolean): If true, we are in "continued grading" mode,
     meaning that the user is continuing to grade even though she has met
     the requirements.
     **/
    installHandlers: function() {
        var sel = $('#openassessment__group-assessment', this.element);
        var view = this;

        // Install a click handler for collapse/expand
        this.baseView.setUpCollapseExpand(sel, $.proxy(view.loadContinuedAssessment, view));

        // Initialize the rubric
        var rubricSelector = $("#peer-assessment--001__assessment", this.element);
        if (rubricSelector.size() > 0) {
            var rubricElement = rubricSelector.get(0);
            this.rubric = new OpenAssessment.Rubric(rubricElement);
        }

        // Install a change handler for rubric options to enable/disable the submit button
        if (this.rubric !== null) {
            this.rubric.canSubmitCallback($.proxy(view.peerSubmitEnabled, view));
        }

        // Install a click handler for assessment
        sel.find('#peer-assessment--001__assessment__submit').click(
            function(eventObject) {
                // Override default form submission
                eventObject.preventDefault();

                // Handle the click
                view.groupAssess();
            }
        );
    },

    /**
     Enable/disable the peer assess button button.
     Check that whether the peer assess button is enabled.

     Args:
     enabled (bool): If specified, set the state of the button.

     Returns:
     bool: Whether the button is enabled.

     Examples:
     >> view.peerSubmitEnabled(true);  // enable the button
     >> view.peerSubmitEnabled();  // check whether the button is enabled
     >> true
     **/
    groupSubmitEnabled: function(enabled) {
        var button = $('#peer-assessment--001__assessment__submit', this.element);
        if (typeof enabled === 'undefined') {
            return !button.hasClass('is--disabled');
        } else {
            button.toggleClass('is--disabled', !enabled);
        }
    },

    /**
     Send an assessment to the server and update the view.
     **/
    groupAssess: function() {
        var view = this;
        var baseView = view.baseView;
        this.groupAssessRequest(function() {
            view.load();
            baseView.loadAssessmentModules();
            baseView.scrollToTop();
        });
    },

    /**
     * Send an assessment to the server and update the view, with the assumption
     * that we are continuing peer assessments beyond the required amount.
     */
    continuedPeerAssess: function() {
        var view = this;
        var gradeView = this.baseView.gradeView;
        var baseView = view.baseView;
        view.groupAssessRequest(function() {
            view.loadContinuedAssessment();
            gradeView.load();
            baseView.scrollToTop();
        });
    },

    /**
     Common peer assessment request building, used for all types of peer assessments.

     Args:
     successFunction (function): The function called if the request is
     successful. This varies based on the type of request to submit
     a peer assessment.

     **/
    groupAssessRequest: function(successFunction) {
        var view = this;
        view.baseView.toggleActionError('group', null);
        view.groupSubmitEnabled(false);

        // Pull the assessment info from the DOM and send it to the server
        this.server.groupAssess(
                this.rubric.optionsSelected(),
                this.rubric.criterionFeedback(),
                this.overallFeedback()
            ).done(
                successFunction
            ).fail(function(errMsg) {
                view.baseView.toggleActionError('group', errMsg);
                view.groupSubmitEnabled(true);
            });
    },

    /**
     Get or set overall feedback on the submission.

     Args:
     overallFeedback (string or undefined): The overall feedback text (optional).

     Returns:
     string or undefined

     Example usage:
     >>> view.overallFeedback('Good job!');  // Set the feedback text
     >>> view.overallFeedback();  // Retrieve the feedback text
     'Good job!'

     **/
    overallFeedback: function(overallFeedback) {
        var selector = '#assessment__rubric__question--feedback__value';
        if (typeof overallFeedback === 'undefined') {
            return $(selector, this.element).val();
        }
        else {
            $(selector, this.element).val(overallFeedback);
        }
    }
};
