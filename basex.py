import os
from BaseXClient import BaseXClient

def add_xml_files_to_database(database_name, xml_files_directory):
    # Connect to BaseX server
    session = BaseXClient.Session('localhost', 1984, 'admin', 'hej123')
    
    try:
        # Open the existing database or create a new one if it doesn't exist
        session.execute("OPEN " + database_name)
    except BaseXClient.CommandError:
        session.execute("CREATE DB " + database_name)
        session.execute("OPEN " + database_name)
    
    try:
        # Iterate over each XML file in the directory
        for filename in os.listdir(xml_files_directory):
            if filename.endswith(".xml"):
                # Read the XML file
                with open(os.path.join(xml_files_directory, filename), "r") as file:
                    xml_data = file.read()
                
                # get name
                tree_name = os.path.splitext(filename)[0]
                
                # add new tree
                session.add(database_name, xml_data, tree_name)
                
                print(f"Added {filename} to the database with tree name {tree_name}.")
        
        print("All XML files added to the database.")
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        # Close the session
        session.close()


def remove_tree_from_database(database_name, tree_name):
    # Connect to BaseX server
    session = BaseXClient.Session('localhost', 1984, 'admin', 'hej123')
    
    try:
        # Open database
        session.execute("OPEN " + database_name)
        
        # Remove the tree
        session.execute("DELETE " + tree_name)
        
        print(f"Tree {tree_name} removed from the database.")
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        # Close the session
        session.close()


if __name__ == "__main__":
    # Name of the existing database
    database_name = "db2"
    
    # Directory containing XML files to be added to the database
    xml_files_directory = "/path/to/xml_files_directory"
    
    # Add XML files to the existing BaseX database
    # add_xml_files_to_database(database_name, xml_files_directory)
    remove_tree_from_database(database_name,"db2")