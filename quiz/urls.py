from django.urls import path

from .views import CreateInvitation, ListAddQuestion, ListAddQuiz, QuizDetail, RespondInvitation, ListAttempt, \
    SubmitAttempt, ListPlayableQuiz, QuizProgress, AttemptProgress

urlpatterns = [
    path("quizzes/creator/", ListAddQuiz.as_view(), name="owned_quizzes"),
    path("quizzes/creator/<uuid:pk>/", QuizDetail.as_view(), name="quiz_detail"),
    path("quizzes/creator/<uuid:pk>/questions/", ListAddQuestion.as_view(), name="quiz_questions"),
    path("quizzes/creator/<uuid:pk>/progress/", QuizProgress.as_view(), name="quiz_progress"),
    path("quizzes/creator/<uuid:pk>/invite/", CreateInvitation.as_view(), name="quiz_invitation"),
    path("quizzes/invitations/<uuid:pk>/", RespondInvitation.as_view(), name="quiz_invitation_response"),
    path("quizzes/", ListPlayableQuiz.as_view(), name="list_playable_quizzes"),
    path("quizzes/<uuid:pk>/", QuizDetail.as_view(), name="view_playable_quizzes"),
    path("quizzes/attempts/", ListAttempt.as_view(), name="quiz_attempt_creation"),
    path("quizzes/attempts/<uuid:pk>/", SubmitAttempt.as_view(), name="quiz_attempt_submission"),
    path("quizzes/attempts/<uuid:pk>/progress/", AttemptProgress.as_view(), name="quiz_attempt_progress"),
]
