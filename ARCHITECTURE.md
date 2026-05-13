**Architectural Summary**

MINGLE adopts a three-tier client-server architecture with a layered backend design and component-based frontend. The **frontend component** (React) runs on each user's **laptop** in their browser and provides the presentation layer, rendering the map interface, user profiles, chat screens, and filtering controls. The frontend communicates with the backend using two protocols: **HTTP requests** for stateless operations including user authentication, bio and profile management, account security, and applying filters, and **WebSocket connections** for real-time, bidirectional communication enabling live features such as map updates, live chat messages, and availability status changes. The **backend component** (Python FastAPI server) runs on a **developer's laptop** and implements the business logic layer, handling user authentication, geolocation-based filtering, privacy rule enforcement, streak calculations, and message routing between connected clients. The **database component** (SQLite) also runs on the **developer's laptop** and provides the data persistence layer, storing user profiles, locations, messages, interests, connection requests, and streaks. The architecture follows a clear separation of concerns: the presentation layer (component-based React frontend) manages user interaction, the business logic layer (Python FastAPI backend) enforces application rules, and the data layer (SQL database) maintains persistent state. Optional external services such as mapping APIs or push notification services may run in the **cloud** and can be invoked via HTTPS from the backend, but are not essential for the core prototype.

**Platforms & Languages**

PLATFORMS  
Frontend

| Platform | Specification | Benefits | Tradeoffs |
| :---- | :---- | :---- | :---- |
| Hardware | Device with a browser (laptop, desktop, tablet, phone) | \- wide range of supported devices \- no hardware cost \- most devices will be able to run the app smoothly | \- most laptops don’t have a GPS chip so location will rely on WiFi (less accurate) \- no control over the quality of device that users will employ |
| Operating systems | Windows, macOS, Linux | \- no specific OS code needed since the browser abstracts OS away \- broad user reach | \- browser behavior might have minor differences across OS/browser combinations |
| Runtime framework | Web browser (Chrome, Safari) | \- user doesn’t have to install an app \- URL is easier to access across devices | \- excessive tabs or other processes in browser may slow map updates |

Backend

| Platform | Specification | Benefits | Tradeoffs |
| :---- | :---- | :---- | :---- |
| Hardware | Developer’s laptop (prototype) / Cloud virtual machine | \- cloud server can be accessed from anywhere at any time  | \- laptop prototype will only work when developer’s laptop is open and active |
| Operating systems | macOS, Windows (prototype) / Linux Ubuntu (cloud) | \- macOS/Windows are familiar to the team, easy to develop locally \- Linux uses fewer resources, team wouldn’t need to handle server administration (all by cloud provider) | \- differences in operating systems may add complexity to development (especially if advancing from prototype) |
| Runtime framework | Python Interpreter & FastAPI | \- Python is familiar to the team, quick to get something working \- FastAPI handles live features, automatically checks for valid data | \- FastAPI is a relatively new framework, less built-in tools than other options and may be harder to debug |

Database

| Platform | Specification | Benefits | Tradeoffs |
| :---- | :---- | :---- | :---- |
| Hardware | Developer’s laptop running SQLite (prototype) | \- no setup needed \- no cloud or internet connection required for development | \- can only run on one machine (developer’s laptop) |
| Operating systems | macOS, Windows (prototype) / Linux Ubuntu (cloud) | \- prototype with familiar systems to the team \- SQLite runs without extra setup (only need Python) \- Linux allows database to run on server that’s always available to all team members | \- prototype only exists on one laptop, makes collaboration hard \- Linux requires internet connection, makes team dependent on Supabase to manage server |
| Runtime framework | SQLite (prototype) / PostgreSQL via Supabase | \- no configuration required for SQLite, works immediately \- Supabase manages Linux environment, team doesn’t have to configure OS | \- queries would have to be rewritten from prototype to product (SQLite to PostgreSQL) |

LANGUAGES

| Language | Benefits | Tradeoffs |
| :---- | :---- | :---- |
| Python (backend) | \- readable \- familiar to the whole team \- can quickly get things working \- big standard library with operations we need | \- environment differences between macOS/Windows teammates can cause inconsistencies |
| React (frontend) | \- component-based, easily maps to Mingle’s pieces \- reusable components \- libraries for maps, live UI, animations | \- unfamiliar to much of the team \- managing state across components can become complex |
| SQL (database) | \- largely familiar to the team \- enforces data integrity (e.g. chat can’t exist without a sender) \- compatible with multiple languages | \- later changes may be disruptive \- complex queries can be hard to debug \- must handle SQL injection attacks |

**Communication Protocols**

Essentially, we have two communication protocols to handle all interactions of our app, Mingle, within total architecture, HTTP requests and Websockets. HTTP requests mainly manage users’ data such as account privacy, updating bios, or more static information that will flow into our database.  Websockets, then mainly in charging of realtime requests such as the user’s stats (is available for meetup or busy), realtime map updating, and all other dynamic information that request effectivity. More details see the table below:

| Communication Protocols | What messages need to be sent and/or requested | Sending messages from where to where | How those messages will be sent |
| :---- | :---- | :---- | :---- |
| HTTP requests  | Static/Persistent Data: Account creation, authentication (Login/Sign-up), bio updates, privacy settings, and profile picture uploads. | Client-to-Server: Initiated by the mobile/web app to the backend API/Database. (Security-related protocol included) | Request-Response Cycle: Sent via standard methods like GET (fetching data) or POST/PATCH (updating data) over a stateless connection. |
| Websockets | Real-time/Dynamic Data: Live location coordinates (GPS), "Available/Busy" status toggles, instant messages, and active map markers. | Bi-directional: Continuous flow between the Client and the Socket Server (and vice versa). | Full-Duplex Stream: Once a "handshake" is established, a persistent connection stays open, allowing data to push instantly without re-requesting. |

**Component Functions & Connector Examples**

**Use Case 1: “User filters map by \#basketball”**

| Step 1 \- User taps Filter icon, selects \#basketball, taps Apply | MapFilter.onApply(selectedTags) \-\> GET/api/map/users?tags=\[basketball\]\&lat=33.64\&lng=-117.84 |
| :---- | :---- |
| Step 2 \- Backend receives filter request | MapService.getNearbyUsers(lat, lng, filters) \-\> SQL: SELECT u.\* FROM users u JOIN user\_tags t ON t.userId=u.id WHERE t.tagId=’basketball’ AND ST\_Distance(u.location, POINT) \< 0.5 |
| Step 3 \- DB returns matched users | Database \-\> { rows: \[{id, displayName, lat, lng, status, tags: \[\]}\] } as JSON to backend |
| Step 4 \- Backend responds to frontend | Backend \-\> 200 { users: \[{id, displayName, lat, lng, status, primaryTag}\] } over HTTPS |
| Step 5 \- Map re-renders with filtered pins | MapView.renderPins(users) \-\> updates map markers, shows count badge |

**Use Case \#2: “User posts a ‘Sunset Hike’ pin”**

| Step 1 \- User taps \+ Pin, fills form, taps Post | PinCreator.onPost(form) \-\> POST /api/pins { title:”Sunset Hike”, tagId: “hiking”, lat: 33.60, lng:-117.83, datetime:”2026-05-16T17:00”, maxParticipants:8 } |
| :---- | :---- |
| Step 2 \- Backend validates \+ saves pin | PinService.createPin(pinData) \-\> SQL: INSERT INTO pins (title, tagId, lat, lng, datetime, hostId, maxParticipants, createdAt) VALUES (...) |
| Step 3 \- DB confirms insert | Database \-\> { id:‘pin\_892’, title:’Sunset Hike’, tagId:‘hiking’, hostId:‘usr\_44’ } as JSON to backend |
| Step 4 \- Backend broadcasts to nearby users | WebSocket.broadcast({ event:‘pin\_created’, pin:{id, title, tagId, lat lng, datetime} }) \-\> all users within 1 mi |
| Step 5 \- User searches ‘walk’, related tags on | MapView.filterPins({ query:‘walk’, showRelated:true }) \-\> GET /api/pins?query=walk\&showRelated=true |
| Step 6 \- Backend returns fuzzy+related results | PinService.searchPins(query, showRelated) → SQL: SELECT \* FROM pins WHERE tagId='walk' OR tagId IN (SELECT relatedTagId FROM tag\_relations WHERE tagId='walk') → { pins:\[{id,title,tagId,lat,lng}\] } |

**Use Case \#3: “New user creates profile with photo”**

| Step 1 \- User selects photo from camera roll | ProfileSetup.onPhotoSelet(file) \-\> validates file.size \< 5MB, else shows error: ‘Image too large. Please choose a file under 5MB.’ |
| :---- | :---- |
| Step 2 \- Frontend uploads photo to storage | S3Client.upload() \-\> PUT https://cdn.mingle.app/photos/{userId} {body: imageBlob, ContentType:’image/jpeg’ } |
| Step 3 \- Storage returns photo URL | S3 → { photoUrl:'https://cdn.mingle.app/photos/usr\_44.jpg' } to frontend |
| Step 4 \- User fills name \+ bio, taps Save | ProfileSetup.onSave(form) → POST /api/profile { displayName:"Alex", bio:"Love hiking", photoUrl, tags:\[\] } |
| Step 5 \- Backend validates \+ saves profile | ProfileService.saveProfile(userId, data) → SQL: INSERT INTO users (id, displayName, bio, photoUrl, createdAt) VALUES (...) — rejects if displayName empty |
| Step 6 \- DB confirms, backend responds | Database → { id:'usr\_44', displayName:'Alex', bio:'Love hiking', photoUrl } → Backend → 201 { success:true, profile:{...} } to frontend |

**Use Case \#4: “User searches and subscribes to \#basketball”**

| Step 1 \- User searches ‘basket’ in tag directory | TagDirectory.onSearch('basket') → GET /api/tags?search=basket\&category=sports |
| :---- | :---- |
| Step 2 \- Backend queries tag table | TagService.searchTags(query, category) → SQL: SELECT id, name, emoji, category FROM tags WHERE name ILIKE '%basket%' AND category='sports' |
| Step 3 \- DB returns matching tags | Database → { tags:\[{id:'tag\_12', name:'basketball', emoji:'🏀', category:'sports'}\] } to backend → frontend |
| Step 4 \- User taps Subscribe on \#basketball | TagDirectory.onSubscribe('tag\_12') → POST /api/tags/subscribe { userId:'usr\_44', tagId:'tag\_12' }  |
| Step 5 \- Backend checks 10-tag limit | TagService.subscribeUserToTag(userId, tagId) → SQL: SELECT COUNT(\*) FROM user\_tags WHERE userId='usr\_44' → if \>= 10 return 400 { error:'Max 10 tags reached' } |
| Step 6 \- Backend saves subscription | SQL: INSERT INTO user\_tags (userId, tagId, subscribedAt) VALUES ('usr\_44','tag\_12', NOW()) |
| Step 7 \- DB confirms frontend updates | Database → { success:true } → frontend adds tag pill to profile view |

**Use Case \#5: “User sets home blackout zone; GPS fails fallback”**

| Step 1 \- User saves home blackout zone | PrivacySettings.onSaveBlackoutZone({ address:'123 Main St', radiusMiles:0.2 }) → POST /api/privacy/blackout { lat:33.65, lng:-117.83, radiusMiles:0.2 } |
| :---- | :---- |
| Step 2 \- Backend saves zone to DB | PrivacyService.saveBlackoutZone(userId, zone) → SQL: INSERT INTO blackout\_zones (userId, centerLat, centerLng, radiusMiles) VALUES (...) |
| Step 3 \- Device OS fires location update | GPS platform → { lat:33.651, lng:-117.831, accuracy:12, timestamp:1747000000 } to LocationManager |
| Step 4 \- Frontend checks blackout locally | LocationManager.onLocationUpdate(coords) → calcDistance(coords, blackoutZones) → if inside zone: suppress POST, hide pin silently |
| Step 5 \- If outside zone: send to backend | LocationManager.sendLocation() → POST /api/location { lat, lng, userId } |
| Step 6 \- Backend verifies \+ broadcasts | LocationService.updateUserLocation(userId, lat, lng) → SQL UPDATE user\_location SET lat,lng,updatedAt → WebSocket.broadcast({ event:'location\_update', userId, lat, lng }) |
| Step 7 \- GPS fails: frontend hides pin | LocationManager.onGPSError() → POST /api/location/hide { userId } → shows banner: 'Location unavailable. You are not visible to others.' |
| Step 8 \- Backend removes user from map | LocationService.hideUser(userId) → SQL: UPDATE users SET locationVisible=false → WebSocket.broadcast({ event:'user\_hidden', userId }) |

**Use Case \#6: “User A requests User B; B accepts; chat opens**

| Step 1 \- User A taps Send Request on User B’s pin | UserPin.onSendRequest({ toUserId:"usr\_77", introMessage:"Want to hike?" }) → POST /api/connections/request { toUserId, introMessage, fromLat, fromLng } |
| :---- | :---- |
| Step 2 \- Backend checks proximity | ConnectionService.sendRequest() → SQL: SELECT lat,lng FROM users WHERE id='usr\_77' → calcDistance(userA, userB) → if \> 0.5mi return 400 { error:'User not in range' } |
| Step 3 \- Backend checks 24 hr cooldown | SQL: SELECT \* FROM connection\_cooldowns WHERE fromId='usr\_44' AND toId='usr\_77' AND expiresAt \> NOW() → if row exists return 400 { error:'Must wait 24h' } |
| Step 4 \- Backend saves request \+ notifies B | SQL: INSERT INTO connection\_requests (fromId, toId, message, status:'pending', createdAt) → FCM/APNs: { to: usr\_77\_deviceToken, title:'New request from Alex', body:'Want to hike?' } |
| Step 5 \- User B taps Accept | RequestInbox.onRespond(requestId:'req\_55', accepted:true) → PATCH /api/connections/request/req\_55 { accepted:true } |
| Step 6 \- Backend opens chat thread | ConnectionService.respondToRequest(requestId, true) → SQL: UPDATE connection\_requests SET status='accepted' → INSERT INTO chat\_threads (userAId:'usr\_44', userBId:'usr\_77', createdAt) |
| Step 7 \- Backend notifies User A | FCM/APNs: { to: usr\_44\_deviceToken, title:'Alex, your request was accepted\!', body:'Start chatting now.' }  |
| Step 8 \- DB confirms, chat opens on both clients | Database → { threadId:'thread\_19', userAId, userBId } → WebSocket pushes { event:'chat\_opened', threadId } to both users |

**Use Case \#7: “User toggles Open to Meet; goes offline mid-toggle”**

| Step 1 \- User taps status toggle to Open to Meet | StatusToggle.onToggle('open') → PATCH /api/users/status { userId:'usr\_44', status:'open' } |
| :---- | :---- |
| Step 2 \- Backend updates DB \+ broadcasts | StatusService.updateStatus(userId, 'open') → SQL: UPDATE users SET status='open', statusUpdatedAt=NOW() → WebSocket.broadcast({ event:'status\_update', userId:'usr\_44', status:'open' }) to nearby users |
| Step 3 \- Map badges update for nearby users | MapView.onStatusUpdate({ userId:'usr\_44', status:'open' }) → re-renders pin badge to green |
| Step 4 \- Connection drops mid-toggle | ConnectionManager.onOffline() → caches { status:'busy', lastLat, lastLng } locally → stops broadcasting location |
| Step 5 \- Server detects disconnect | StatusService.onUserDisconnect('usr\_44') → SQL: UPDATE users SET status='busy', lastSeen=NOW() → WebSocket.broadcast({ event:'user\_offline', userId:'usr\_44' }) |
| Step 6 \- Messages queued in inbox | SQL: INSERT INTO user\_inbox (toUserId:'usr\_44', fromUserId, message, receivedAt) — held until reconnect, no push notification sent |
| Step 7 \- User reconnects, inbox flushed | StatusService.onUserReconnect('usr\_44') → GET /api/inbox → { messages:\[{from, body, timestamp}\] } delivered to client |

**Use Case \#8: “Streak increments on message; resets after 7 days**

| Step 1 \- User A sends message to User B | ChatView.onSend({ threadId:'thread\_19', body:'See you tomorrow\!' }) → POST /api/messages { threadId, body } |
| :---- | :---- |
| Step 2 \- Backend saves message | MessageService.saveMessage(threadId, fromId, body) → SQL: INSERT INTO messages (threadId, fromId, body, sentAt) VALUES (...) |
| Step 3 \- Backend triggers streak check | StreakService.onMessageSent('usr\_44','usr\_77') → SQL: SELECT \* FROM streaks WHERE (userA='usr\_44' AND userB='usr\_77') |
| Step 4 \- DB returns current streak row | Database → { id:'strk\_8', count:13, lastMessageAt:'2026-05-03' } to backend |
| Step 5 \- Backend increments streak | if NOW() \- lastMessageAt \< 7 days: SQL UPDATE streaks SET count=14, lastMessageAt=NOW() WHERE id='strk\_8' → UPDATE leaderboard SET streakScore=14 WHERE userId='usr\_44' |
| Step 6 \- Cron job fires after 7-day lapse | StreakService.runDailyExpiry() → SQL: SELECT \* FROM streaks WHERE lastMessageAt \< NOW()-7days → UPDATE streaks SET count=0, resetAt=NOW() → FCM/APNs: { title:'Streak ended with Bob', body:'Send a message to start fresh\!' } |
| Step 7 \- User opens Leaderboard tab | LeaderboardView.onLoad() → GET /api/leaderboard?limit=50 |
| Step 8 \- Backend queries rankings | LeaderboardService.getRankings(50) → SQL: SELECT userId, displayName, streakScore FROM leaderboard ORDER BY streakScore DESC LIMIT 50 → { rankings:\[{ rank, userId, displayName, streakScore }\] } |

**Reflection**

Over the course of this assignment we better defined the requirements and translated them into a three-tier architecture. We made concrete decisions for each layer: React on the frontend for its component-based structure and map library support, FastAPI on the backend for its built-in async and WebSocket capabilities, and SQLite for  its local persistence during prototyping. We decided to split our communication protocols between HTTP (for static operations like profile updates and authentication) and WebSockets (for live map updates and status changes). This was one of our most important design choices, and working through the eight use cases helped us see where the boundary would exist. Building the prototype made those abstract decisions tangible, and how the filter logic connects directly to the tag-subscription model we defined in the requirements.  
Our current prototype runs entirely on one teammate’s machine, which works for demonstration but will require migrating to a persistent database and a deployed server before real user testing can happen. We plan to extend the prototype with the connection request and chat flow, and begin evaluating what a transition from SQLite to a cloud-hosted database would look like for the next stage.
