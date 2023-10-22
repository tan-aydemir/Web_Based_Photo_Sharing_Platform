# PhotoShare Web Application

**Table of Contents**

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Customizing](#customizing)
- [Contributing](#contributing)
- [License](#license)

## Introduction

PhotoShare is a web application that allows users to share photos, manage albums, add friends, comment on photos, and more. It is built using Flask, a Python web framework, and utilizes a MySQL database for data storage. This README file will guide you through the installation and usage of the application.

## Features

- User authentication (login and registration).
- Uploading and managing photos with captions.
- Creating and managing photo albums.
- Adding friends to your network.
- Tagging photos with keywords.
- Liking and commenting on photos.
- Viewing popular tags and photos by tags.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python**: Make sure you have Python installed (3.x recommended).

- **Flask**: Install the Flask web framework using `pip install flask`.

- **MySQL**: You need a MySQL database. Install MySQL and create a database named "photoshare."

- **Flask-MySQL**: Install Flask-MySQL using `pip install flask-mysql`.

- **Web Server**: You need a web server to run the application. The application is set up to run on `localhost` by default.

- **Dependencies**: Check the `requirements.txt` file and install the required Python packages using `pip install -r requirements.txt`.

## Installation

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/yourusername/photoshare.git
   ```

2. Navigate to the project directory:

   ```bash
   cd photoshare
   ```

3. Create a MySQL database named "photoshare."

4. Import the database schema by executing the SQL script provided in the project folder.

   ```bash
   mysql -u yourusername -p photoshare < photoshare.sql
   ```

5. Configure the application by editing the `app.py` file. Update the database connection details, secret key, and any other configurations as needed.

6. Run the application:

   ```bash
   python app.py
   ```

7. Access the web application in your web browser at `http://localhost:5000`.

## Usage

- **Registration**: Visit the registration page to create an account.

- **Login**: After registration, you can log in with your credentials.

- **Uploading Photos**: You can upload photos to your profile and create albums.

- **Adding Friends**: Add friends to your network by providing their email addresses.

- **Tagging Photos**: Tag your photos with keywords to categorize them.

- **Commenting and Liking**: You can comment on photos and like them.

- **Viewing Popular Tags**: Check out the most popular tags.

- **Viewing Friends' Photos**: View photos uploaded by your friends.

## Project Structure

- **app.py**: The main application file containing the Flask application code.

- **templates**: This directory contains HTML templates for the web pages.

- **static**: Static files like CSS, JavaScript, and images are stored here.

## Customizing

You can customize the application by modifying the HTML templates and stylesheets in the `templates` and `static` directories. You can also extend the functionality by editing the `app.py` file.

## Contributing

Contributions are welcome! If you'd like to contribute to the project, feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Feel free to modify this README file to suit your specific project's needs. Provide detailed instructions for installation, usage, and any customizations. Additionally, include information about the project's license and how others can contribute to it.
