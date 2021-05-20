# firewall-rule
This action will create and update a Firewall rule in GCP.

## Inputs


### `name`

**Rquired** The Name of the firewall rule.


### `tcp`

**Required** TCP ports to open (comma separated, for ranges use e.g.: 2000-2500).


### `source`

**Required** The Source IP address (comma separated, CIDR notated).


### `tags`

**Required** The target tags (comma separated). 

### `network`

**Required** The target Network.

### `Project`

**Required** The gcp project id.

### `udp`

**Optional** The gcp project id.
**Default** ''

### `description`

**Optional** Description of the firewall rule.
**Default** ''


## Outputs

### `json_out`

The json representation of the firewall rule. Could be an empty map


## Example Usage
```
uses: EngelVoelkers/github-actions/gcp/firewall-rule@master
with:
  name: 'my-fw-rule'
  tcp: '443,2000-2500'
  source: '1.2.3.4/32,4.3.2.1/32'
  tags: 'mytag01,mytag02'
  network: 'my-vpc-network'
  project: 'my-fancy-project-id'
  udp: '60000'
  description: 'Used for my super service'
```
