MINGLE
Team Member Name - UCInetID
Arjun Vivek - viveka3
Chloe Keirn - ckeirn
Andrew Ji - jia4
Katrina Yichen Wang - yichw58
Yanjie Li - yanjiel5



Executive Summary: 
This app is a location-based social discovery platform designed for people who want to meet others nearby with shared interests in the real world. Think of a live map of people around you, filtered by what you're into: whether that's hiking, coffee, chess, or e-scooters. Instead of scrolling through profiles or swiping, users can see who's physically nearby and open to connecting right now.
The core audience is socially active individuals, which includes college students, hobbyists, and anyone who finds it hard to meet people organically in a new city or environment. The app is especially well-suited for campuses, parks, urban neighborhoods, and events where people with shared interests naturally congregate but rarely connect.
The app's primary goal is to lower the entry barrier for real-world connection. Users are able create a profile in a few quick steps by adding a photo, bio, and a set of interest tags drawn from a directory of interests we have curated based on trends. They can see other users on a live map, filter by shared interests or availability, and send a connection request if they’re within a specific proximity to start a private chat. Every interaction is consent-driven and location sharing is off by default, availability defaults to "Busy," and connection requests require explicit acceptance before a chat opens.
The main key features our app is going to have are interest-based discovery via a standardized tag system, a live map with user-controlled location sharing and privacy rules (including time-based schedules and blackout zones), proximity-gated connection requests with optional intro messages, persistent private messaging, an availability status toggle, and a streak and leaderboard system to incentivize daily engagement.
The app assumes users have smartphones with GPS capability and an active internet connection. All location data is treated as sensitive, and the system is designed with user control and privacy as non-negotiable defaults throughout.


Application Context / Environmental Constraints: 
The app will be live for download on iOS and Android smartphones through the respective app stores and is built for the real world wherever people actually are (parks, campuses, coffee shops). It needs GPS, a data connection, camera/photo library access, and push notifications to function properly.
On the backend it leans on platform location services, a mapping SDK like Google Maps, push notification routing through APNs and FCM, a real-time data layer for live map and chat updates, and cloud storage for profile photos.
A few real constraints would be the map experience is pretty thin if not many users are nearby, GPS gets kind of rough and shaky when indoors or in dense urban areas with a lot of people using common internet services, and continuous location usage and sharing can drain battery fast. The app needs to handle spotty connections gracefully and make sure to default to safe states (location hidden, status cached) rather than doing anything unexpected when the signal drops.


Functional Requirements: 
Users can subscribe to multiple interests
Overview: The system should allow users to select multiple interests that pertain to them. These interests will be specified through hashtags (e.g. #hiking, #coffee) that users can subscribe to through a directory of all available interests. They can select a checkbox to the left of the interest to display profiles with the same interest on the map, or they can click the profile icon to the right of the interest to add it to their profile.
Interests that a user subscribes to appear in their profile under their bio.
Users should begin at 0 interests when they first join the app.
User-defined filtering criteria
Overview: When looking at the map, users should be able to filter which profiles they can see. Filters include: interests, availability status (open to meetup/busy).
Users can filter by multiple interests. If they select multiple, they can view profiles with any combination of those interests. For example, if a user selects #biking and #surfing they can see users who subscribed to #biking, #surfing, or both #biking and #surfing (among their other interests).
Users can put filters on both interests and availability status. In this case, it will only display users with those interests and availability status. For example, if a user filters by the #food interest and “Open to Meetup” status, they will only see users with both of those criteria (not #food without “Open to Meetup” or “Open to Meetup” without #food).
Filters should reset every time the user opens the app.
User bios
Overview: Users have the option to write a bio for themselves when they create their account. It will appear in their profile in a box under their profile picture and username.
If the user chooses not to write a bio, text “This user has not written a bio yet.” will appear in the bio section of the profile.
The top right corner of the bio box will contain an “Edit” button where the user can enter a new bio or change their existing one.
Closed set of developer-defined interests
Overview: The system should use a predefined, closed set of tags (e.g. ‘#escooter, #ebike) to categorize content, users, and activities. The tag list is created, maintained, and controlled exclusively by the developers, and end users are not permitted to create new tags. Each tag will have a display name, an emoji icon, and category to support organization. The full tag list is browsable in a searchable tag directory within the app.
Limits on location sharing. 
Overview: The system must ensure that all location sharing is fully controlled by the user. Location sharing is disabled by default with the user having to manually turn their location on. If location sharing is enabled, the user can choose who can access their location, such as specific individuals or groups, and the system must strictly enforce these rules so no unauthorized user can view the data.
Users can set a time-based sharing schedule (e.g. share location from 10 a.m. until 9 p.m.).
At any point, the user must be able to disable location sharing at any time through a simple and accessible control. This action must immediately remove all location sharing and the user is removed from the live map and is invisible from others.
Connection requests and chat
Overview: when two users are within a certain range of each other (e.g. 5 mile radius), they will have the option to request a chat with another user. Once in range of other users, they can click on their icon on the map and their profile will pop up, showing their profile. This allows users to see what interests they subscribed to, their user bios, and profile picture. If one user sends a request and if the other user accepts this request, they will be directed to a private chat thread where users can message one another. 
Upon sending a request there will be an option to send an optional message (max 100 characters).
Chat persists even after the users leave the range with each other. Users can continue to have a conversation regardless of their location.
Availability Status (Open to meetup/Busy)
Overview: Users will have a tag on their profile displaying whether or not they are open to meeting up or are currently busy and not available. This status is a user-controlled field that can be updated at any time and is intended to help other users quickly understand whether interaction or in person connection is appropriate.
Each user must have exactly one active status at a time, selected from a predefined set (e.g., “Open to meetup,” or “Busy”). The default state should be set to Busy to protect user privacy and prevent unintended availability. The system must ensure that status changes take effect immediately and are reflected in real time across parts of the app, such as profiles, search results, and maps.
The status should be clearly displayed on the user's profile. 
Streaks
Overview: The system will contain a “streaks” feature that tracks everyday user activity, meant to increase interaction between users. Whenever a user sends a message to another profile, the sending user’s streak extends. The profile they send to can either be someone they have never talked to before or an existing friend.
The user’s current streak is initially displayed when they open the app on a new day. As soon as they send a message to someone, a popup appears indicating that the streak was extended.
The user’s current streak is always displayed in an icon on their profile.
A leaderboard should be available in another tab to show rankings for users with the longest streaks. This is meant to encourage users to engage with each other in interest of the leaderboard.


Functional Requirements Analyses:
Users can subscribe to multiple interests
Pros: This feature maximizes opportunities for users to interact with each other. With multiple interests available, interaction can happen between users with any combination of interests as long as they share at least one. Additionally, users feel included and encouraged to use the app; having more interests increases the likelihood of other users sharing some of them, which is exciting for people trying to find friends with similarities.
Cons: Interests could get saturated with people who clicked the interest purely for more visibility to other users. Chats and meetups could be less meaningful if users have limited interest in their personal tags. Excessive amounts of tags in a user profile could make their main interests unclear.
Ethical concerns: Users could be judged for their interests and have the potential to receive unkind messages in response.
User-defined filtering criteria
Pros: Users can easily find others with specific interests, which increases likelihood of chats and meetups. Certain users can be more visible due to less cluttered profiles on the map. Users don’t have to filter through users who aren’t available when they want to meet up.
Cons: Users have less chances to meet diverse groups of people if they always use strict filters. Filters could also increase the app’s complexity; if users can’t figure out how to change filters or forget that they have them applied, it hinders their overall experience and ability to meet others.
Ethical concerns: Filtering people out based on interests could reinforce biases that users hold towards people with certain interests.
User bios
Pros: Users can freely express themselves in their profiles and add more information that they couldn’t with just their name/picture/interest tags. Looking at other users’ bios can help users decide if they want to pursue a chat or meetup (makes it easier to see what the other person is like). Makes the app more personalized.
Cons: Writing a bio could seem like too much effort for some users, which may make their profile less engaging. Without detail on their profile, other users may feel less compelled to contact them and their activity on the app could be negatively affected.
Ethical concerns: Excessive freedom with what users can write in their bios could lead to concerns of inconsiderate, rude, or hateful remarks in those bios. 
Closed set of developer-defined interests 
Pros: Some of the pros of this feature include being easy to manage and effective in classifying and organizing different user interests and data. Because all users select from the same standardized list, it becomes much easier to search, filter and match with others who share similar interests. This reduces confusion caused by duplicate or slightly different tags, for example ‘#bike’ vs ‘#biking’ vs. ‘#cycling’ and leads to more accurate results.
Cons: Some of the cons of this feature include limiting the expressiveness of user interests. Some niche or hyper-specific features may not be included within the set of tags which makes this feature not representative of everyone’s interests. Also, the developer team must continually update the tag list to make it stay relevant, requiring constant maintenance. 
Ethical concerns: The main ethical concern is that there is going to be a bias in representation. Since developers are the ones controlling what tags exist, they also indirectly decide which interests are visible or valued on the app. Different cultures value different activities and it is impossible to fully incorporate all of the interests in the world. This could unintentionally exclude certain demographics, cultures, or less mainstream activities. 
Limits on location sharing 
Pros: Limiting location sharing provides strong privacy protection, which is a main priority for our app. Users can decide exactly who sees their location and avoid exposing sensitive information to strangers or unintended audiences. 
Cons: People may think that having to remember to turn on and turn off their location is too much work. People can also forget to turn off their location at times when they don't want other people to see their location.
Ethical concerns: A major concern is user safety and consent. The system should make sure that location sharing is always voluntary and cannot be enabled without permission.
Connection requests and chats
Pros: Users having to manually request and accept chats is beneficial because the person who is receiving requests can choose who they want to talk to as opposed to automatically receiving chat messages. Choosing who you want to connect with results in better matches and more meaningful interactions.
Cons: There is potential for spam or excessive requests and users may feel overwhelmed by too many incoming requests, which can reduce the overall experience. Chats can also make it feel like there is pressure to respond, making some users uncomfortable.
Ethical concerns: A key concern is user safety and harassment prevention. There should be measures to filter messages to protect users from harmful interactions.
Availability Status (Open to Meetup / Busy)
Pros: An availability status provides clear and immediate communication of a user’s intentions. Instead of guessing whether someone is open to interaction, other users can quickly understand their availability, which makes coordinating meetups more efficient and reduces awkward or unwanted requests. It also gives users a sense of control over social interaction.
Cons: A status of just “Open” or “Busy” may be too simplistic to fully capture a user’s situation. For example, a user might be open to chatting but not meeting in person, or only available at certain times, which the system does not fully represent.
Ethical Concerns: Displaying availability may unintentionally pressure users to engage, especially if others interpret “Open to Meetup” as an obligation to respond or participate.
Streaks
Pros: Users are encouraged to use the app on a daily basis to keep their streak going. If users keep coming back every day, they get more opportunities to meet people. The leaderboards implement a popular game aspect that provides a sense of competition which keeps users motivated.
Cons: Interactions could become minimal if users send meaningless messages just to keep the streak alive. The sense of competition that the streak leaderboard imposes could take away from the main goal of the app in forming and maintaining friendships.
Ethical concerns: Users without long streaks could feel inferior to those higher on the streak leaderboard, which could discourage them from getting back onto the app.


Use Cases:
Multiple Interest Subscriptions & Filtering
User Goal: Filter the map to see only users who share their current activity of interest.
Basic Flow: User is subscribed to #basketball, #chess, and #hiking. They are at a park and want to find someone to play basketball with. They tap the Filter icon, select #basketball, and tap Apply. The map now shows only nearby users subscribed to #basketball. They spot a match 0.3 miles away.
Alternative Flow: User applies a filter for #basketball and Open to Meet status. Only two users remain visible on the filtered map. The user taps one profile to view it and decides to send a connection request.
Exceptional Flow 1: User applies a filter that returns zero results. The map displays: "No users match your current filters nearby. Try expanding your range or removing a filter." The user removes the status filter and two results appear.
User-defined filtering criteria. 
User Goal: Announce a planned activity and find others to join.
Basic Flow: User opens the map and taps the + Pin button. They fill in: Title: “Sunset Hike”, Tag: #hiking, Location: Crystal Cove State Park, Date/Time: Saturday 5:00 PM, Description: “Easy 2-mile trail, all welcome!”, Max participants: 8. They tap Post. The pin appears on the map for all nearby #hiking users. Three users RSVP within an hour. Then other users can filter certain activities and meetups based on the hashtags included in the example above. And a feature called “show related tags” can be toggled in order to show related activities.
Alternative Flow: Users might type a wrong tag, the filtering system then also showing some related activities based on users’ inputs. When a user tries to look for some activities related to talk but accidentally type it as “walk”. The filtering system will display results of “walk” if the “show related tags” toggled on.
Exceptional Flow: Users might forget to or didn’t include any tags for certain posts. Then the filtering system can not find such posts for targeting users.
User Bios 
User Goal: Create a profile so others can learn about their interests before sending a connection request. 
Basic Flow: User opens the app for the first time and then creates an account. They are prompted to complete their profile. They upload a photo from their camera roll, enter a display name, write a short bio, type in their hobbies, and tap Save. Their profile is now visible to matched users on the map.
Alternative Flow: User skips the favorite song field and taps Save without filling it in. The app accepts the incomplete profile (only display name and photo are required) and marks the optional fields as empty. The profile is saved successfully.
Exceptional Flow 1: User attempts to upload a profile picture that exceeds the file size limit (5MB). The app displays an error message: "Image too large. Please choose a file under 5MB." The user selects a smaller image and the upload succeeds.
Exceptional Flow 2: User attempts to save the profile without filling in any information. The placeholder of the name turns red and there should be a pop up model displaying an error message:”Please fill in the necessary information.” The user clicks on “back to editing” and creates the profile successfully by filling in the “name” placeholder.
Closed Tag Subscriptions
User Goal: Subscribe to interest tags to appear on the map and find matches.
Basic Flow: User opens the tag directory, browses the Sports category, and taps #basketball and #tennis to subscribe. Both tags are added to their profile. Their map pin now displays a basketball emoji (their selected primary tag). They appear on the map to other users subscribed to #basketball or #tennis.
Alternative Flow: User searches for "pickleball" in the tag directory. The tag does not exist. The app displays: "Tag not found. Want to suggest it?" with a link to a feedback form. The user subscribes to #tennis as the closest alternative.
Exceptional Flow: User attempts to subscribe to an 11th tag after already having 10 active subscriptions. The app displays: "You can subscribe to a maximum of 10 tags. Please remove one before adding another." The subscription is not added.
Location Sharing Limits
User Goal: Protects privacy and prevents their location from being shared when users don’t want to.
Basic Flow: User goes to Settings > Privacy > Blackout Zones and taps Add Zone. They search for their home address, set a 0.2-mile radius, and save. From now on, when the user is within 0.2 miles of home, their location is automatically hidden from the map, even if location sharing is otherwise enabled.
Alternative Flow: User sets a time-based sharing schedule of 8am–10pm. At 10:01pm, the app automatically disables their location sharing and removes them from the map. The user receives a push notification: "Location sharing paused for the night."
Exceptional Flow: User's device GPS fails while they are outside their blackout zone. The app detects that location data is unavailable and automatically removes the user's pin from the map. A banner in the app reads: "Location unavailable. You are not visible to others."
Connection Request & Chat
User Goal: Sending requests for a meetup between two matched users upon a certain range.
Basic Flow: App send a message to User A that User B (matched with the same tags, #hiking) is within 0.5 miles and whose status is “Open to Meet”. User A then is able to view User B’s Bios and send a few messages (the maximum attempts could be modified through privacy settings) to ask User B whether willing to do some activities. After User A successfully sends such a message, User B will receive such message and if User B replies to such message, a chat thread opens for both users.
Alternative Flow: User A sends a message requesting to User B. User B’s status changes to Busy before who sees the notification. User B still receives the request and can accept or decline. If accepted, chat opens normally.
Exceptional Flow: User A sent a message requesting but User B declined. User A receives a friend-request-denied (so sad~) notification. The chat will not open. User A cannot send another request to User B for 24hours. (During this time, user B can still send a message requesting to User A to accept in order to prevent misclick.)
Availability Status: ? Open to Meet : Busy
User Goal: Signal to nearby users that they are available or not for spontaneous activities.
Basic Flow: User arrives at some places. Who taps the status toggle at the top of ui to set one’s self to “Open to Meet” status. Then, the ui’s functional map interface will update the user’s badge to green to inform other nearby users. Other nearby users sharing the same hashtags can now see their Open to Meet status and seed message requesting. Later, the user might set status back to Busy, and then the user’s badge turns to gray or disappears from the map. (User can decide to achieve which behavior to in privacy settings) 
Alternative Flow: Users switch one’s status from Open to Meet to Busy while the internet connection is bad. The local client will stop sharing the user's location, mute any message requesting and the server will use the latest cached status. However, other users might not see laggy users’ status updating immediately, so they can still send the message requesting. Users will not receive those messages directly. Those messages will be stored in the user’ inbox and no notification will be sent to the user. When internet connection is stable, the status then updates to the latest correct status.
Exceptional Flow: User forgot to set the status to Busy, the app client detects inactivation and automatically sets the status to Busy. No messages received directly during this time and will be stored in the user’s inbox.
Streaks & Leaderboard
User Goal: Maintain a streak with a connection made through our App.
Basic Flow: User A and User B met through our App last week and have been chatting. It has been 6 days since their last message. User A receives a reminder notification: “Your streak with User B expires in 24 hours! Send a message to keep it going.” User A sends a message. The streak increments to 2 weeks.
Alternative Flow: User A wants to see how their streak compares with others. They open the Leaderboard tab and see a ranked list of users by highest active streak. User A is ranked #47 with a 4-week streak. They tap their own entry to see which of their connections contribute to their streak count.
Exceptional Flow: User A and User B go 8 days without exchanging a message. The streak resets to 0. Both users receive a notification that looks something like "Your streak with [name of person] has ended. Start a new one by sending a message!" The leaderboard updates to reflect the reset.
