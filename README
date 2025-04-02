# Cribl Lookup File Transfer
This Python scrpt facilitates the transfer of lookup files between Cribl worker groups

## Features
- Transfer lookup files between Cribl worker groups
- Support for both CSV (.csv) and GZIP (.gz) file formats
- Configuration via command-line arguments or INI file
- Automatic create or update of lookup files
- Commit and deploy funcationality
- Comprehensive error handling

## Prerequisites
- Python 3.6+
- Required packages:
  ```bash
  pip install requests
  ```
## Installation
1. Clone the respository:
```bash
git clone https://github.com/StacySimmons/cribl-lookup-transfer.git
cd cribl-lookup-transfer
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
## Configuration
The script can be configured using either command-line arguments or a configuration file.
### Config File (config.ini)
Create a ```config.ini``` file in the same directory as the script with the following format:
```ini
[cribl]
client_id = your_client_id
client_secret = your_client_secret
organization_id = your_organization_id
lookup_filename = the_lookupfile.csv
source_worker_group = default_search
target_worker_group = default
```
### Command Line Arguments
All configuration options can be specified via command-line-arguments, which override config file values
- ```--config```: path to configuration file (default: config.ini)
- ```--client-id```: Cribl client ID
- ```--client-secret```: Cribl client secret
- ```--organization-id```: Cribl.cloud Organization ID
- ```--lookup-file```: lookup file name
- ```--source-group```: source worker group
- ```--target-group```: target worker group

## Usage
### Basic Usage with Config File
```bash
python cribl_lookup_transfer.py
```
### Using Command Line Arguments
```bash
python cribl_lookup_transfer.py --client-id "abc" --client-secret "xyz" --lookup-file "data.csv"
```
### Mixed Approach
```bash
python cribl_lookup_transfer.py --config myconfig.ini --lookup-file "new_data.gz"
```
### Full Help
```bash
python cribl_lookup_transfer.py --help
```
## Workflow
1. Authenticates with Cribl Cloud API using client credentials
2. Checks for lookup file existence in source worker group
3. Download the file from source worker group
4. Uploads the file to target worker group
5. Creates or updtes the lookup file configuration
6. Commits the changes
7. Deploys the cdhanges to the target worker group

## File Format Support
- ```.csv```: Standard CSV files (Content-Type: text/csv)
- ```.gz```: GZIP compress files (Content-Type: application/gzip)

The script automatically detects the file type based on the extension and set the appropriate content type.

## Error Handling
The script includes comprehensive error handling and will:
- Print detailed error messages for API failures
- Exit with status code 1 on any failure
- Handle both network and configuration errors

## Contributing
1. Fork the repository
2. Create your feature branch (```git checkout -b feature/amazing-feature```)
3. Commit your changes(```git commit -m 'Add some amazing feature'```)
4. Push to the branch(```git push origin feature/amazing-feature```)
5. Open an Pull Request

## License
- Feel free to modify and distribute

## Acknowledgements
- Built for and with the Cribl.cloud API
- Thanks to the Python community for excellent libraries