# User Interface Mockups and Analysis  
### Create Account / Log In  
<img width="1440" height="1024" alt="create account" src="https://github.com/user-attachments/assets/e29f0d51-b9c4-449a-998f-1366890fe96d" />
<img width="1440" height="1024" alt="log in" src="https://github.com/user-attachments/assets/9e871c74-3c3f-4e60-b7ae-dd282aca6ec6" />
The “Create an Account” screen is what the user first sees when they open the website. Assuming they don’t have an account yet, they can make one by clicking on each box and typing a username, email, and password, then pressing “SIGN UP” in blue. If they already have an account and just aren’t logged in, they click the “LOG IN” button and are brought to the popup on the second screenshot. There, they can input their username and password and log in to their existing account. There is also an “X” in the top right corner of the popup that allows them to view the map without making an account.

### Main Screen   
<img width="1440" height="1024" alt="main" src="https://github.com/user-attachments/assets/1578de16-eaa7-4248-8b14-f433d7a41e2b" />
Once the user logs in, they are brought to the main screen. They mainly see a map that they can drag by holding down left-click and moving their mouse, or zoom in/out using the \+/- button in the top left corner. The circles in the middle of the map represent nearby users and their locations, which the user can click on to expand their profile. There are multiple features in the header, all of which are clickable buttons: a chat button, which opens a chat sidebar; an “Open to Meet” / “Busy” indicator where the user can signify their status; a “Filters” button which opens a filter sidebar; and their profile picture in the top right corner which opens the currently logged in user’s profile details.

### Filter Sidebar  
<img width="1440" height="1024" alt="filter sidebar" src="https://github.com/user-attachments/assets/96a8fb69-c198-4546-80c3-ca8c7b5688bc" />
When the user clicks on the “Filters” button, it opens a sidebar on the left side of the screen that lets the user select filters of attributes that they want the visible profiles to have. There is an “AVAILABILITY” section where they can choose between people that are “Open to Meet,” “Busy,” or “All.” They can also select any number of interest tags that they want between all that are available. Only profiles with all selected tags will be visible.

### Chat Sidebar  
<img width="1440" height="1024" alt="chat sidebar" src="https://github.com/user-attachments/assets/60d7840c-6d5c-4e7b-8768-5922162a3de6" />
When the user presses the chat button, a chat sidebar opens on the right side of the screen. There, the user can see the chats that they have with current friends. When they click on one of their available users, it opens a popup on the bottom of the sidebar that shows their recent messages with that user. They can send a message on the bottom by typing in the “Write message here…” box and clicking the send icon to the right.

### View Another User’s Profile  
<img width="1440" height="1024" alt="profile (unadded)" src="https://github.com/user-attachments/assets/165988ff-18cc-46a8-8f67-74e6de06e514" />
<img width="1440" height="1024" alt="profile (requested)" src="https://github.com/user-attachments/assets/76fac218-140e-4688-9b74-8f11d5a1c0db" />
<img width="1440" height="1024" alt="profile (added)" src="https://github.com/user-attachments/assets/27c75620-8a79-40e8-9be8-1c0348d13e81" />
These screenshots show the popup that appears when a user clicks on someone else’s profile circle on the main map. It shows a circle with their profile picture, under which they can find their name and status \- either “Open to Meet” or “Busy.” To the right of that, they see an icon that shows their friend status with the user. For strangers, there’s a blue icon with a plus in the corner to indicate that they can request to friend them. If they press that icon, the plus switches to a clock and text displays “Request sent.” Once that friend accepts the request, it changes to a green icon with a checkmark to indicate that they’re friends. Below these features, the profile has a bio and their listed interests.

### View / Edit Personal Profile  
<img width="1440" height="1024" alt="edit user profile" src="https://github.com/user-attachments/assets/9c2946f3-7565-446c-a5c8-b03776562ebb" />
When the user presses the icon in the top right corner, it opens the current user’s profile and allows them to edit it. If they click the plus icon, they can add a profile picture. If they click the pencil on either their name or their bio, they can edit those aspects. By clicking the plus next to their current interests, they can add more interests.

### Add Interests to Profile  
<img width="1440" height="1024" alt="add interests" src="https://github.com/user-attachments/assets/0c0515f6-7c88-4cec-ab7e-4a499698601b" />
This menu appears when the user clicks on the plus to add more interests to their bio. They can search for available interests or click on any available ones to add them to their profile. The scrollbar on the side allows them to look for more. They can tell which interests they’ve already added by their blue color in the interest search popup.

# Heuristic Evaluation
### Visibility of system status

The three profile states – unadded, requested, and added – are the best example of status visibility in our design. The button label changes from ‘Connect’ to ‘Request Sent’ to showing a connected state, so users know exactly where they stand with another person. Additionally, the Open to Meet / Busy toggle in the navigation bar is also always visible, so users know their current broadcast status at a glance. When users open one of the sidebars or popups, such as the chat, filters, or profile, that icon changes color so they know what they have opened and where they can close it.

### Match system words to the real world

The filter sidebar uses plain category headers (Availability, Sports, Social) rather than database field names to keep it familiar for everyday users. Tags like \#basketball, \#hiking, and \#yoga use everyday words with emojis, which feel natural to people who hear those words regularly and can associate them with the emoji visual. ‘Open to Meet’ and ‘Busy’ are real world status phrases that any user can understand when they see it. The profile card label ‘BIO’ and ‘INTERESTS’ are familiar from social apps users already know.

### User control and freedom

We let the users control their own availability status that can be toggled on/off instantly with no confirmation needed. Every modal (create account, log in, and all three profile card states) has a clear X button in the top right corner. This feature is visible and consistent which gives users a clear exit at all times, whether they finished their desired action or didn’t mean to open a certain menu. The filter sidebar can be closed without applying changes. The chat sidebar is a panel rather than a full-screen takeover, so the map is always reachable. Users can close the filters and chat sidebars by clicking the altered icons where they originally opened them.

### Consistency and standards

The navy/dark navigation bar is consistent across every screen (main, filter open, chat open, all three profile states, and edit profile). This gives the app a reliable frame that users can always orient from. The circular avatar with initials is used consistently across profile cards and the chat sidebar, creating a unified visual language for user identity. Many of the interface properties reflect those of other apps, such as the “Create and Account” and “Log In” screens with familiar fields for the user to fill out (username, email, password).

### Error prevention

The profile create account screen has a confirm password field, which prevents common account creation errors such as mistyped passwords from occurring before submission. The filter sidebar uses radio buttons for Availability (only one option selectable at a time), preventing contradictory filter states like selecting both ‘Open to Meet’ and ‘Busy’ simultaneously.

### Recognition rather than recall

The tag directory is fully browsable by category, users do not need to know a tag exists to find it. The map filter shows what filters people can choose from and see what's applied so they don’t have to remember what filters they applied. User profiles show what their interests are so users immediately see what they have in common with someone.

### Accelerators

The availability toggle is in the navbar on every screen – users never need to navigate anywhere to change their status. The filters button is also always accessible from the navbar, not buried in a settings menu. Tapping a map pin goes directly to the profile card with a connect action, which is a fast 2 step flow: tap in, tap connect.

### Minimalist design

The main map screen only shows the main things: the map, filter button, chat button, profile, and availability toggle. This makes it easier for the user to navigate the app as it is very minimalistic with few buttons. All of the different UI interfaces have the bar at the top which creates consistency and alignment. Profile cards on the map show only name, primary tag, and status, not a full bio. The “Create an Account,” “Log In,” and profile screens all make screens 

### Help users recognize and recover from errors

The three-state profile card (unadded \-\> requested \-\> added) inherently helps users recover from accidental taps. They can see their current state clearly and understand what happened. The X button on all modals gives an immediate escape if a user opens the wrong screen. Editing capabilities on the user’s profile allows them to change anything they didn’t intend to add while displaying what their profile currently looks like.

### Help and documentation

The create account screen includes ‘Already a member? LOG IN’, which is a helpful contextual link that guides users who ended up on the wrong screen. The filter sidebar’s visual grouping (Availability, Sports, Social) acts as implicit documentation. Users can understand the categories without needing a label. All of the features are largely self-explanatory with familiar icons, names, and navigation.
