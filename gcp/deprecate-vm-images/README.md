# deprecate-vm-images
This action will deprecate all Images of a specific OS Family in favor of a new one.
All Images will be marked as DEPRECATED and configured to get deleted in n days (default 10 Days)

## Inputs


### `replacement`

**Rquired** The Name of the new image used as a replacement


### `os_family`

**Required** The Name of the OS Family


### `project`

**Required** The project of the images


### `delete_in`

**Optional** The Days when the deprecated images should be deleted 

**Default** 10d


## Outputs

### `deleted_images`

The Number of deprecated VM Images. Could be zero or more.


## Example Usage
```
uses: EngelVoelkers/github-actions/gcp/deprecate-vm--images@master
with:
  replacement: 'my-fancy-new-image'
  os_family: 'my-fancy-os-family'
  project: 'my-fancy-project-id'
  delete_in: '20d'
```
