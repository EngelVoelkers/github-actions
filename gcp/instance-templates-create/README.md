# instance-templates-create
This action will create an instances template that you can use for creating
Instances and Instances Groups. It will download a script from a URL and use this
as a vm startup script.


## Inputs


### `name`

**Rquired** The Name of the new template



### `region`

**Required** The region of the new template



### `project`

**Required** The project of the new template



### `network`

**Required** The Network used for VMs created with this template 



### `sub_network`

**Required** The Subnet used for VMs created with this template



### 'machine_type'

**Required** The Machine Type used for VMs created with this template



### `image_family`

**Optional** The name of the image-family to use. If image-family or image is 
not given, the project Default Image Family will be used (e.g. debian-10). 



### `image`

**Optional** The name of the image to use. If image or image-family 
is not given, the project Default Image Family will be used (e.g. debian-10).



### `image_project`

**Optional** The project where the image or image family is located. If not 
given the template project will be used.



### `labels`

**Optional** Comma delimited list of key=value pairs.



### `scopes`

**Optional** Comma delimited list of GCP scopes.



### `tags`

**Optional** Comma delimited list of network tags.



### `startup_script`

**Optional** The http path to a startup script file.


## Example Usage
```
uses: EngelVoelkers/github-actions/gcp/instance-templates-create@master
with:
  name: 'my-fancy-new-template'
  region: 'europe-west1'
  project: 'my-fancy-project-id'
  network: 'my-fancy-network'
  sub_network: 'my-fancy-subnet'
  machine_type: 'e2-micro'
  image_family: 'my-fancy-image-family'
  image_project: 'my-fancy-image-project'
  labels: 'app=fancy,hipp=star
  tags: 'fancy-network-tag'
```
