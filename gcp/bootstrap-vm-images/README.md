# bootstrap-vm-images
This action will create a VM image. It will download and execute the given script
within the bootstrapper VM.


## Inputs


### Argument:`image_name`

**Rquired** `The Name of the Image`


### Argument:`zone`

**Required** `The gcp zone to use.`


### Argument:`network`

**Required** `The network id to use.`


### Argument:`machine_type`

**Required** `The compute machine type to use`


### Argument:`subnetwork`

**Required** `The subnetwork id to use.`


### Argument:`tags`

**Optional** `The (Network) Tags to use.`


### Argument:`project`

**Required** `The GCP project to use`


### Argument:`scopes`

**Optional** `The VM scopes needed while executing the script.`


### Argument:`labels`

**Optional** `The Labels you want to assign to the creating VM.`


### Argument:`from_image`

**Optional** `The base image you want to fork from.`

**Default**: `debian-10`


### Argument:`from_image_project`

**Optional** `The project where the base image is located.`

**Default**: `debian-cloud`


### Argument: `script`

**Required** `The url of the script you want to use to provision your image`


### Argument: `variables`

**Optional** `Define comma delimited key=value pairs that gets exported to the script as environment variables.`


### Argument: `os_family`

**Required** `The os family used to store the new image.`


## Example Usage
```
uses: EngelVoelkers/github-actions/gcp/bootstrap-vm-images@master
with:
    image_name: 'My-fancy-image'
    zone: 'europe-west1-b'
    network: 'my-fancy-network'
    machine_type: 'e2-standard-2'
    subnetwork: 'my-fancy-subnetwork'
    tags: 'tag1,tag2,tag3'
    project: 'my-fancy-project'
    scopes: 'https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/pubsub,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append'
    labels: 'key1=value1,key2=value2'
    from_image: 'debian-10'
    from_image_project: 'debian-cloud'
    script: 'https://${{ secrets.GITHUB_TOKEN }}@raw.githubusercontent.com/my-company/my-repo/my-branch/path-to-file/filename'
    variables: 'var1=value1,var2=value2,SUPER_IMPORTANT=sure'
    os_family: 'my-fancy-os-family-name'
```
