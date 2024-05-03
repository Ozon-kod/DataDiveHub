from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


# Reading the data inside the xml file to a variable under the name  data
with open('divedatafile.xml', 'r') as f:
    data = f.read() 

# Passing the stored data inside the beautifulsoup parser 
bs_data = BeautifulSoup(data, 'xml') 

# Finding all instances of tag   
b_unique = bs_data.find_all('equipment') 
print(b_unique) 

#Using find() to extract attributes of the first instance of the tag 
b_name = bs_data.find('manufacturer') 
print(b_name) 

# Extracting the data stored in a specific attribute of the `child` tag 
value = b_name.get('id') 
print(value)

def get_depth():
    y=[]
    depth_data= bs_data.find_all("depth")
    for depth_tag in depth_data:
        depth_tag=depth_tag.string.strip("</depth >")
        depth_tag=float(depth_tag)
        y.append(depth_tag)
        return y


def get_time():
    x=[]
    time_data=bs_data.find_all("divetime")
    for k in time_data:
        k=k.string.strip("</divetime> ")
        k=float(k)
        x.append(k)
        return x

x = get_time()
y = get_depth()

plt.plot(x, y)
plt.show()