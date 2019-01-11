#The client_secrets OAuth file has been deleted from repository.Create your own OAuth file by the same name for google-signin. 

#This file describes how to navigate and run the application

1.Go in your /fullstack-nanodegree-vm/vagrant/catalog directory.
(link for cloning directory:https://github.com/udacity/fullstack-nanodegree-vm)                              
2.Bring up your virtual machine using vagrant up and vagrant ssh commands.
3.Go the /vagrant/catalog directory.
4.Run the command 'python flaskapp.py'.
5.Now your server is up and running.
6.Go to your browser and type the url 'http://localhost:5000/catalog' to go to the homepage.

--------------------------------------------------------------------------------------------
#This part describes the navigation in your application.

1.Once you are on the homepage login using your google signin account using the link in top right corner of your application.
2.If your 'http://localhost:5000/login' url does not show the signin button refresh the page or navigate back and try again.
3.You can click on any one of the category to see all the items in it.
4.Once logged in you can add a item using link on the homepage.
5.Once logged in you can see the json of an item if you click on it.
6.Once logged in you can also see the contents of the database using the json endpoint.
7.Once logged in you can click on any item to see its details along with functionality to edit or delete it.
8.Remember that you must be the one to create the item in order to delete or edit it else it will show you an alert message.
9.If you are not logged in you can only see the list of existing categories,their corresponding items and details of the item.

-----------------------------------------------------------------------------------------------
Json structure:
For the json structure of the categories each record contains:
1.name
2.id
3. Each Item for that category and their attributes

For the json structure for each item each record contains:
1.name
2.id
3.price
4.description
5.category_id