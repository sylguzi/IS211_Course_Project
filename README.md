Blogs that allows user to register, and submit new posts:
- User can register
- User has to log in to submit new posts
- User can only edit his own posts
- User are unique by name
- User can publish, unpublish, delete, edit an existing post
- Unlogged user can see a list of all the published posts
- Unlogged user can see a published post by clicking on the title

Basically all actions except viewing publish post require the user to be logged in and has a pre-check to check whether he is or not.

The user can register itself by hitting register and filling the form with an unique name.
There is no restriction on the password except being empty.
A post has to have a title and a content.

All information is stored in sqlite:
- Account: for users
- Post: for posts
- Category: for categories
