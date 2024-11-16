
// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js');

// Initialize Firebase app with your Firebase config
firebase.initializeApp({    
    apiKey: "AIzaSyAPE-nwaHWcCQJy3CmH9jWv8jCZFYXna9s",
    authDomain: "todo-app-11873.firebaseapp.com",
    projectId: "todo-app-11873",
    storageBucket: "todo-app-11873.appspot.com",
    messagingSenderId: "1029086662942",
    appId: "1:1029086662942:web:df169f068e8bd520a6790f",
    measurementId: "G-NKHQ8GP41Z"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage(function(payload) {
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: payload.notification.icon
    };

    return self.registration.showNotification(notificationTitle, notificationOptions);
});
