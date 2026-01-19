# COLA Cloud CLI

Command-line interface for the [COLA Cloud API](https://colacloud.us) - Access the TTB COLA Registry from your terminal.

COLA Cloud provides access to the United States TTB (Alcohol and Tobacco Tax and Trade Bureau) Certificate of Label Approval registry, containing over 1 million alcohol product label records.

## Installation

```bash
# Install with pip
pip install colacloud-cli

# Or with uv
uv pip install colacloud-cli

# Or install from source
git clone https://github.com/cola-cloud-us/colacloud-cli.git
cd colacloud-cli
uv sync
```

After installation, the `cola` command will be available.

## Quick Start

1. **Get your API key** from [https://app.colacloud.us](https://app.colacloud.us)

2. **Configure the CLI:**
   ```bash
   cola config set-key
   # Enter your API key when prompted
   ```

3. **Start searching:**
   ```bash
   cola colas search "buffalo trace"
   ```

## Commands

### Configuration

```bash
# Set your API key (prompts for input)
cola config set-key

# Set API key directly
cola config set-key --key "your-api-key"

# Show current configuration (API key is masked)
cola config show

# Clear configuration
cola config clear
```

You can also set the `COLACLOUD_API_KEY` environment variable instead of using the config file.

### COLAs

Search and retrieve COLA (Certificate of Label Approval) records.

```bash
# Full-text search
cola colas search "buffalo trace"

# List with filters
cola colas list --product-type wine --origin california

# Filter by date range
cola colas list --date-from 2024-01-01 --date-to 2024-12-31

# Filter by ABV
cola colas list --product-type "distilled spirits" --abv-min 40 --abv-max 50

# Search by brand name
cola colas list --brand "maker's mark"

# Pagination
cola colas list -q "bourbon" --limit 50 --page 2

# Get detailed information about a specific COLA
cola colas get 24001234

# Output as JSON (for scripting)
cola colas list -q "whiskey" --json | jq '.data[].brand_name'
```

#### COLA Search Options

| Option | Description |
|--------|-------------|
| `-q, --query` | Full-text search query |
| `--product-type` | Filter by type: `malt beverage`, `wine`, `distilled spirits` |
| `--origin` | Filter by country/state |
| `--brand` | Filter by brand name (partial match) |
| `--date-from` | Minimum approval date (YYYY-MM-DD) |
| `--date-to` | Maximum approval date (YYYY-MM-DD) |
| `--abv-min` | Minimum ABV percentage |
| `--abv-max` | Maximum ABV percentage |
| `--limit` | Results per page (max 100) |
| `--page` | Page number |
| `--json` | Output as JSON |

### Permittees

Search and retrieve permittee (alcohol producer/importer) records.

```bash
# Search by company name
cola permittees list -q "diageo"

# Filter by state
cola permittees list --state KY

# Filter by active status
cola permittees list --state CA --active
cola permittees list --state NY --inactive

# Get detailed information about a specific permittee
cola permittees get NY-I-136

# Output as JSON
cola permittees list -q "distillery" --json
```

#### Permittee Search Options

| Option | Description |
|--------|-------------|
| `-q, --query` | Search by company name |
| `--state` | Filter by state (e.g., CA, NY, KY) |
| `--active/--inactive` | Filter by active status |
| `--limit` | Results per page (max 100) |
| `--page` | Page number |
| `--json` | Output as JSON |

### Barcode Lookup

Look up products by their barcode (UPC, EAN, etc.).

```bash
# Look up by UPC
cola barcode 012345678901

# Look up by EAN
cola barcode 5000281025155

# Output as JSON
cola barcode 012345678901 --json
```

### Usage Statistics

Check your API usage and limits.

```bash
# Show usage stats
cola usage

# Output as JSON
cola usage --json
```

## Output Examples

### COLA List

```
$ cola colas search "buffalo trace"
+------------+-----------------+-----------------------+------------------+------------+
| TTB ID     | Brand           | Product               | Type             | Approved   |
+============+=================+=======================+==================+============+
| 24001234   | Buffalo Trace   | Kentucky Straight...  | distilled spirits| 2024-01-15 |
| 23098765   | Buffalo Trace   | Single Barrel...      | distilled spirits| 2023-12-01 |
+------------+-----------------+-----------------------+------------------+------------+
Showing 1-2 of 156 results (page 1 of 8)
```

### COLA Detail

```
$ cola colas get 24001234
+----------------------------------------------------------+
|                        24001234                           |
|                                                          |
|  Buffalo Trace                                           |
|  Kentucky Straight Bourbon Whiskey                       |
+----------------------------------------------------------+

Basic Information
  Product Type    distilled spirits
  Class           Whiskey
  Origin          Kentucky
  ABV             45.0%
  Volume          750 ml

Dates & Status
  Application     2024-01-10
  Approval        2024-01-15
  Status          approved

Permit Information
  Permit Number   KY-DSP-0019
  Application     Original Label
```

### Usage Stats

```
$ cola usage
+--------------------------------------------------+
|              API Usage Statistics                 |
+--------------------------------------------------+

  Tier              standard
  Current Period    2024-01
  Monthly Usage     1,234 / 10,000 (12.3%)
  Remaining         8,766
  Rate Limit        60 requests/minute
```

## JSON Output

All commands support `--json` flag for scripting and piping to other tools:

```bash
# Get all bourbon brands
cola colas list -q "bourbon" --json | jq -r '.data[].brand_name' | sort | uniq

# Count COLAs by product type
cola colas list --json | jq '.data | group_by(.product_type) | map({type: .[0].product_type, count: length})'

# Export permittees to CSV
cola permittees list --state KY --json | jq -r '.data[] | [.permit_number, .company_name, .company_state] | @csv'
```

## Configuration

The CLI stores configuration in `~/.colacloud/config.json`. The file is created with restrictive permissions (mode 600) to protect your API key.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `COLACLOUD_API_KEY` | API key (takes precedence over config file) |

## Development

```bash
# Clone the repository
git clone https://github.com/cola-cloud-us/colacloud-cli.git
cd colacloud-cli

# Install dependencies
uv sync

# Run the CLI in development
uv run cola --help

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [COLA Cloud Website](https://colacloud.us)
- [API Documentation](https://colacloud.us/docs/api)
- [GitHub Repository](https://github.com/cola-cloud-us/colacloud-cli)
