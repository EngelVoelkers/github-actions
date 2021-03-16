# keep-n-docker-images
Keep only "n" of the latest docker images in the gcp registry of a project.

## Inputs

### `image`

**Required** The Name of the base image (without any tag or sha checksum)

## `max`

**Required** How many latest Images keep at max?

**Default** 10


## Outputs

### `deleted_images`

The Number of deleted Docker Images. Could be zero or more.


## Example Usage
```
uses: EngelVoelkers/github-actions/gcp/keep-n-docker-images@master
with:
  image: 'eu.gcr.io/my-fancy-project/my-image-name'
  max: '42'
```
