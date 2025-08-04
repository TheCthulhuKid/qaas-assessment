import nested_admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Avg
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.html import format_html

from . import models


class ChoiceInline(nested_admin.NestedTabularInline):
    model = models.Choice
    extra = 4
    max_num = 4
    fields = ["text", "is_correct", "order"]
    sortable_field_name = "order"
    ordering = ["order"]


class QuestionInline(nested_admin.NestedStackedInline):
    model = models.Question
    extra = 1
    fields = ["text", "question_type", "order", "points"]
    ordering = ["order"]
    sortable_field_name = "order"
    inlines = [ChoiceInline]
    show_change_link = True


@admin.register(models.Quiz)
class QuizAdmin(nested_admin.NestedModelAdmin):
    list_display = [
        "title",
        "owner",
        "status",
        "total_questions",
        "total_attempts",
        "created_at",
        "action_buttons",
    ]
    list_filter = ["status", "created_at", "owner"]
    search_fields = ["title", "owner__username"]
    readonly_fields = [
        "id",
        "created_at",
        "modified_at",
        "total_questions",
        "total_attempts",
        "average_score",
    ]
    inlines = [QuestionInline]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "description", "owner", "status")},
        ),
        (
            "Timing",
            {
                "fields": (
                    "start_time",
                    "end_time",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": ("total_questions", "total_attempts", "average_score"),
                "classes": ("collapse",),
            },
        ),
        (
            "System Information",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        """Automatically set the creator to the current user"""
        if not change:  # Only for new objects
            obj.creator = request.user
        super().save_model(request, obj, form, change)

    @admin.display()
    def total_questions(self, obj):
        return obj.questions.count()
    total_questions.short_description = "Questions"

    @admin.display()
    def total_attempts(self, obj):
        return obj.attempts.count()
    total_attempts.short_description = "Attempts"

    @admin.display()
    def average_score(self, obj):
        avg = obj.attempts.filter(status="completed").aggregate(avg_score=Avg("score"))[
            "avg_score"
        ]
        return f"{avg:.1f}" if avg else "N/A"
    average_score.short_description = "Avg Score"

    def action_buttons(self, obj):
        """Custom action buttons"""
        view_invitations = (
                reverse("admin:quiz_invitation_changelist")
                + f"?quiz__id__exact={obj.id}"
        )
        view_attempts = (
                reverse("admin:quiz_attempt_changelist") + f"?quiz__id__exact={obj.id}"
        )

        return format_html(
            '<a class="button" href="{}">View Invitations</a>&nbsp;'
            '<a class="button" href="{}">View Attempts</a>',
            view_invitations,
            view_attempts,
        )

    action_buttons.short_description = "Actions"
    action_buttons.allow_tags = True


@admin.register(models.Invitation)
class QuizInvitationAdmin(admin.ModelAdmin):
    list_display = [
        "quiz",
        "participant",
        "status",
        "invited_by",
        "created_at",
        "responded_at",
    ]
    list_filter = ["status", "created_at", "quiz"]
    search_fields = ["participant__username", "quiz__title", "invited_by__username"]
    readonly_fields = ["id", "created_at", "responded_at"]

    def save_model(self, request, obj, form, change):
        """Automatically set the invited_by to the current user"""
        if not change:  # Only for new objects
            obj.invited_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.Attempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "quiz",
        "status",
        "score_display",
        "created_at",
        "completed_at",
        "action_buttons",
    ]
    list_filter = ["status", "created_at", "quiz"]
    search_fields = ["participant__username", "quiz__title"]
    readonly_fields = [
        "id",
        "created_at",
        "completed_at",
        "score",
        "max_score",
        "percentage_score",
    ]

    fieldsets = (
        (
            "Attempt Information",
            {"fields": ("quiz", "participant", "status")},
        ),
        ("Scoring", {"fields": ("score", "max_score", "percentage_score")}),
        ("Timing", {"fields": ("created_at", "completed_at")}),
        ("System Information", {"fields": ("id",), "classes": ("collapse",)}),
    )

    @admin.display()
    def score_display(self, obj: models.Attempt):
        if obj.score is not None and obj.max_score is not None:
            percentage = obj.percentage_score
            return f"{obj.score}/{obj.max_score} ({percentage}%)"
        return "Not scored"
    score_display.short_description = "Score"

    def action_buttons(self, obj):
        """Custom action buttons"""
        view_answers = (
            reverse("admin:quiz_answer_changelist")
            + f"?attempt__id__exact={obj.id}"
        )

        return format_html('<a class="button" href="{}">View Answers</a>', view_answers)

    action_buttons.short_description = "Actions"
    action_buttons.allow_tags = True


@admin.register(models.Answer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = [
        "attempt",
        "question_preview",
        "selected_choice_preview",
        "is_correct",
        "answered_at",
    ]
    list_filter = ["answered_at", "attempt__quiz"]
    search_fields = ["attempt__participant__username", "question__text"]
    readonly_fields = ["answered_at", "is_correct"]

    @admin.display()
    def is_correct(self, obj: models.Answer) -> bool:
        return obj.selected_choice.is_correct

    @admin.display()
    def question_preview(self, obj: models.Answer) -> str:
        return truncatechars(obj.question.text, 50)
    question_preview.short_description = "Question"

    @admin.display()
    def selected_choice_preview(self, obj: models.Answer) -> str:
        if obj.selected_choice:
            return truncatechars(obj.selected_choice.text, 50)
        return "No answer"
    selected_choice_preview.short_description = "Selected Answer"


admin.site.register(models.QuizUser, UserAdmin)
