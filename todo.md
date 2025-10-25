# MEGA TODO

- Sistema de usuarios HECHO
- Sistema de tokens HECHO
- Torneos
- Predicciones // Prode
- Leaderboards por torneo y global (endpoint)
- Logica de puntos (servicio de puntos)


--- Backend ---
-✅ service to calculate users points on each prediction
-✅ modify prediction model to also use attribute points on the prediction, which can be nullable and update predictions services accordingly update daily_task to also calculate new points value for each prediction
-✅ logic to not be able to update or create predictions after fixture has already started (use match date, not status, as it can be outdated due to only updating database once a day with the daily_task cronjob)
-✅ make endpoints for updating all of 1 tournament info
-✅ make so that users that are not part of the tournament not able to access any of the endpoints that are not related to explictly joining it
-✅ make endpoint get tournaments where user is joined, not necessarily the user has to have created it, replace the endpoint of /tournaments/my
- modify auth/jwt utils to have methods for get_current_user, get_optional_current_user (can return None), and update EVERY ENDPOINT THAT REQUIRES THIS to use those methods for getting the user. An example of how to do this is already in tournaments.py in blueprints/api

<!-- - try to make a migration system or add information on how to do it on migration.md -->
<!-- - integrate that migration system on main.py -->
<!-- - update users to have global points that sum every league points (update model) -->
<!-- - make service to calculate all of that -->

--- Frontend ---
- update fixtures displays to also show the new attribute points in the prediction, if prediction doesn't exists and the match has already finished, show '-' in the prediction display and 0 points, otherwise, use api info
- create a new page in tournaments where you can access your tournaments, and also make tournaments accesible by ID as there is a is_public argument, so to access private tournaments
- when you click on one of the tournaments you are part of it should redirect you to a page with info of the tournament, in this case just the leaderboard
- using new points system, create a leaderboard component to be able to show how many points each member of a tournament has
- make admin of tournament in my tournaments section be able to configure the tournament settings, he can modify tournament's name, description and privacy, this can be done through a config button inside of the my tournaments button for each of the configurable tournaments of the user
- in the navbar, next to the username, show his total points attribute