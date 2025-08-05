# Quiz as a Service (QaaS)

A quiz application that allows users to create quizzes, invite participants via real-time notifications, and track quiz performance. Built with Django and WebSockets for real-time interactions.

## Features

- **Quiz Management**: Create, edit, and manage quizzes with multiple-choice questions
- **Real-time Invitations**: Send quiz invitations to participants with instant WebSocket notifications
- **Interactive Responses**: Accept or decline invitations in real-time
- **Quiz Attempts**: Track and manage quiz attempts with detailed scoring
- **Performance Analytics**: View quiz statistics and participant performance

## Technologies Used

- **Backend**:
  - Django 4.x
  - Django REST Framework
  - Django Channels (WebSockets)
  - Channels Redis (for WebSocket backend)
  - PostgreSQL (database)
  - Daphne (ASGI server)

- **Testing**:
  - pytest
  - pytest-django
  - pytest-asyncio (for WebSocket testing)

## Requirements

- Python 3.13+
- PostgreSQL
- Redis (for WebSocket channel layers)
- Docker and docker-compose (for containerized deployment)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone git@github.com:TheCthulhuKid/qaas-assessment.git qaas
   cd qaas
   ```

2. Configure environment variables in `.env` file:
   ```
   # Example .env file
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_PASSWORD=password
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   ```

3. Build and start the containers:
   ```bash
   docker-compose up
   ```

   This will create a superuser with the credentials specified in the `.env` file.

4. Access the application at http://localhost:8000

## Usage

### Admin Interface

Access the admin interface at `/admin/` to manage quizzes, questions, users, and more.

### API Endpoints

The application provides a RESTful API for interacting with the quiz system:

#### Authentication
- `POST /api-token-auth/`: Obtain an authentication token

#### Quiz Management
- `GET /api/quizzes/creator/`: List all quizzes created by the authenticated user
- `POST /api/quizzes/creator/`: Create a new quiz
- `GET /api/quizzes/creator/<uuid:pk>/`: Get details of a specific quiz
- `PUT/PATCH /api/quizzes/creator/<uuid:pk>/`: Update a quiz
- `GET /api/quizzes/creator/<uuid:pk>/questions/`: List all questions for a quiz
- `POST /api/quizzes/creator/<uuid:pk>/questions/`: Add a question to a quiz
- `GET /api/quizzes/creator/<uuid:pk>/progress/`: Get quiz statistics and progress

#### Invitations
- `POST /api/quizzes/creator/<uuid:pk>/invite/`: Invite a user to take a quiz
- `GET/PATCH /api/quizzes/invitations/<uuid:pk>/`: View or respond to an invitation

#### Quiz Taking
- `GET /api/quizzes/`: List all quizzes available to the authenticated user
- `GET /api/quizzes/<uuid:pk>/`: Get details of a specific quiz for taking
- `GET /api/quizzes/attempts/`: List all quiz attempts by the authenticated user
- `PATCH /api/quizzes/attempts/<uuid:pk>/`: Submit answers for a quiz attempt
- `GET /api/quizzes/attempts/<uuid:pk>/progress/`: Get progress of a specific attempt

### WebSocket Communication
#### I got help with the javascript
The application uses WebSockets for real-time communication:

#### Connection
Connect to the WebSocket endpoint:
```javascript
const socket = new WebSocket(`ws://${window.location.host}/ws/invitations/`);
```

With authentication token:
```javascript
const socket = new WebSocket(`ws://${window.location.host}/ws/invitations/?token=${authToken}`);
```

#### Receiving Messages
Listen for incoming messages:
```javascript
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'invitation') {
        // Handle new invitation
        console.log(`Received invitation to quiz: ${data.quiz_title}`);
    } else if (data.type === 'invitation_response') {
        // Handle invitation response
        console.log(`User ${data.participant} has ${data.status} your invitation`);
    } else if (data.type === 'response_confirmation') {
        // Handle confirmation of our own response
        console.log(`Your response has been recorded: ${data.status}`);
    }
};
```

#### Sending Responses
Respond to invitations:
```javascript
socket.send(JSON.stringify({
    'type': 'invitation_response',
    'invitation_id': invitationId,
    'status': 'accept'  // or 'decline'
}));
```

## Testing

The project includes tests for models, views, and WebSocket consumers. (I ran out of time for the serializers)

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/quiz/test_models.py

# Run with verbose output
python -m pytest -v
```
