import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from IPython.display import clear_output
import csv

# Define a function to extract recipe ingredients and steps
def ingredients_steps():
  fractions_dict = {"½": ".5", "⅓": ".33", "⅔": ".67", "¼": ".25", "¾": ".75", "⅕": ".2", "⅖": ".4", "⅗": ".6", "⅘": ".8", "⅙": ".16", "⅚": ".83", "⅛": ".13", "⅜": ".38", "⅝": ".63", "⅞": ".88"}
  # Check if the list of ingredients is not empty
  if len(ingredient_list_items)!= 0:

    # Create an empty list to store the extracted ingredients
    ingredients = []

    # Loop through each ingredient list item and extract its information
    for ingredient in ingredient_list_items:

      # Create an empty dictionary to store the extracted ingredient information
      ingredient_dict = {}

      # Try to extract the quantity of the ingredient, otherwise leave it blank
      try:
        quantity = ingredient.find('span', {'data-ingredient-quantity': True}).text.strip()
        for sign, value in fractions_dict.items():
                    quantity = quantity.replace(sign, value)
      except:
        quantity = ''

      # Try to extract the unit of the ingredient, otherwise leave it blank
      try:
        unit = ingredient.find('span', {'data-ingredient-unit': True}).text.strip()
      except:
        unit = ''

      # Extract the name of the ingredient
      name = ingredient.find('span', {'data-ingredient-name': True}).text.strip()

      # Add the extracted information to the ingredient dictionary
      ingredient_dict['quantity'] = quantity
      ingredient_dict['unit'] = unit
      ingredient_dict['name'] = name

      # Add the ingredient dictionary to the list of extracted ingredients
      ingredients.append(ingredient_dict)

    # Find all the step list items and extract their information
    step_list_items = soup.find_all('li', class_= 'comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup')

    # Create an empty dictionary to store the extracted steps
    steps = {}

    # Loop through each step list item and extract its information
    for i, step in enumerate(step_list_items):

      # Find the step text and extract it, otherwise leave it blank
      step_text = step.find('p', {'class': 'comp mntl-sc-block mntl-sc-block-html'})
      if step_text is not None:
        steps[i+1] = step_text.text.strip()

    # Create a dictionary to store the extracted recipe information
    recipe_dict = {
        "name": recipe_name,
        "ingredients": ingredients,
        "steps": steps
    }

    # Append the recipe dictionary to the list of recipes
    return recipe_list.append(recipe_dict)


# Define a function to extract links from the current page and add them to the same domain links list
def link_addition():

  # Extract all links from the current page
  new_page_links = [link.get('href') for link in soup.find_all('a')]

  # Extract all recipe card links from the current page
  new_recipe_card_links = [link.get('href') for link in soup.select('.mntl-card-list-items')]

  # Combine the links into a single list
  new_links = new_page_links + new_recipe_card_links

  # Loop through each link, check if it belongs to the same domain, and add it to the same domain links list if it is not already there
  for new_link in new_links:
    if new_link and new_link.startswith(url) and new_link not in same_domain_links:
      same_domain_links.append(new_link)
      pbar.total = len(same_domain_links)
      pbar.refresh()

  # Update the progress bar description
  return pbar.set_description(f'{recipe_name} {len(recipe_list)}')


# Define a function to format the extracted recipe data into a consistent format
def format_data(data):

  # Create an empty list to store the formatted recipe data
  formatted_data = []

  # Loop through each recipe in the data and format its information
  for entry in data:

    # Create a dictionary to store the formatted recipe information
    formatted_entry = {
        "Recipe Name": entry["name"]
    }

    # Loop through each ingredient in the recipe and add it to the formatted entry
    for idx, ingredient in enumerate(entry["ingredients"], start=1):
      formatted_entry[f"Ingredient {idx} name"] = ingredient["name"]
      formatted_entry[f"Ingredient {idx} unit"] = ingredient["unit"]
      formatted_entry[f"Ingredient {idx} quantity"] = ingredient["quantity"]

    # Loop through each step in the recipe and add it to the formatted entry
    for idx, step in entry["steps"].items():
      formatted_entry[f"Step {idx}"] = step

    # Add the formatted entry to the list of formatted recipe data
    formatted_data.append(formatted_entry)

  # Return the list of formatted recipe data
  return formatted_data

# Define a function to write the formatted recipe data to a CSV file
def write_to_csv(formatted_data, filename):

  # Determine the fieldnames for the CSV file from the formatted data
  fieldnames = sorted(set(key for row in formatted_data for key in row))

  # Open the CSV file for writing and write the header row
  with open(filename, mode="w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Loop through each row of formatted data and write it to the CSV file
    for row in formatted_data:
      writer.writerow(row)


# Define some variables to store the current state of the program
counter = 0
checkpoint_frequency = 500

# Define some URLs to start the web scraping from
start_url = "https://www.allrecipes.com/recipes/"
url = "https://www.allrecipes.com/recipe"

# Set the headers to be used in the HTTP requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Send a GET request to the start URL and extract its content
response = requests.get(start_url, headers=headers)
html_content = response.content

# Parse the HTML content using Beautiful Soup
soup = BeautifulSoup(html_content, "html.parser")

# Extract all the links from the start page
page_links = [link.get('href') for link in soup.find_all('a')]

# Extract all the recipe card links from the start page
recipe_card_links = [link.get('href') for link in soup.select('.mntl-card-list-items')]

# Combine the links into a single list
links = recipe_card_links + page_links

# Filter the links to include only those that belong to the same domain as the recipe URL
same_domain_links = [link for link in links if link and link.startswith(url)]

# Create an empty list to store the extracted recipes
recipe_list = []

# Create a progress bar to track the scraping progress
pbar = tqdm(same_domain_links)

# Loop through each link and extract the recipe information from the corresponding web page
for i, link in enumerate(pbar):

    # Checkpoint the program every time the number of extracted recipes is a multiple of the checkpoint frequency
    if len(recipe_list) % checkpoint_frequency == 0:
      
      # Format the extracted recipes and write them to a CSV file
      formatted_data = format_data(recipe_list)
      write_to_csv(formatted_data, f"recipe_checkpoint_{checkpoint_frequency}.csv")
      
      # Update the counter
      counter += checkpoint_frequency
      
    # Send a GET request to the current link and extract its content
    response = requests.get(link, headers=headers)
    html_content = response.content

    # Parse the HTML content using Beautiful Soup
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract the recipe name from the URL
    path_parts = link.split('/')
    recipe_name = path_parts[-2].replace('-', ' ').title()

    # Extract the list of ingredients from the web page and store it in the recipe list
    ingredient_list_items = soup.find_all('li', class_='mntl-structured-ingredients__list-item')
    ingredients_steps()

    # Extract the links from the current web page and add them to the same domain links list
    link_addition()

    # Clear the output to update the progress bar
    clear_output(wait=True)

