# COLA Cloud CLI

Command-line interface for the [COLA Cloud API](https://colacloud.us) - Access the TTB COLA Registry from your terminal.

COLA Cloud provides access to the United States TTB (Alcohol and Tobacco Tax and Trade Bureau) Certificate of Label Approval registry, containing millions of label approval records.

COLA Cloud is an independent service that turns public TTB label approvals into searchable, enriched data. An approval record is not a unique product or proof of current retail availability. See the [product-data workflow and source limits](https://colacloud.us/product-enrichment) and [California wine recipe](https://colacloud.us/data/california-wine).

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

3. **Retrieve one California-origin wine approval in a fixed date scope** (requires `jq`):
   ```bash
   cola colas list --product-type wine --origin California \
     --date-from 2026-08-01 --date-to 2026-08-31 --limit 1 --json > colas.json
   ttb_id=$(jq -r '.data[0].ttb_id // empty' colas.json)
   if [ -n "$ttb_id" ]; then cola colas get "$ttb_id" --json; fi
   ```
   An empty result is valid. This is one page of approval records, not all wines or proof of current sale.

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

# Filter by package and derived category
cola colas list --category Beer --derived-subcategory "Beer > Ale" \
  --container-type can --volume-unit "fluid ounces" --volume-min 12 --volume-max 16

# Search generic text, including applicant/company names
cola colas list -q "molson coors"

# Sort text searches by OpenSearch relevance score
cola colas list -q "bourbon" --sort relevance_desc

# Pagination
cola colas list -q "bourbon" --limit 50 --page 2

# Retrieve the ID discovered in the quickstart
cola colas get "$ttb_id"

# Output as JSON (for scripting)
cola colas list -q "whiskey" --json | jq '.data[].brand_name'
```

#### COLA Search Options

| Option | Description |
|--------|-------------|
| `-q, --query` | Generic text query across brand, product, permit, applicant/company, and related text |
| `--product-type` | Filter by TTB type: `malt beverage`, `wine`, `distilled spirits`; can be used multiple times |
| `--category` | Filter by derived category: `Beer`, `Wine`, `Liquor`; can be used multiple times |
| `--derived-subcategory` | Filter by derived category path prefix, such as `Beer > Ale` |
| `--origin` | Exact recorded country/state name; not business address or appellation |
| `--domestic-or-imported` | Filter by `domestic` or `imported` |
| `--status` | Filter by application status |
| `--brand` | Filter by brand name (partial match) |
| `--permit-number` | Filter by exact permit number |
| `--barcode` | Filter by exact main barcode value |
| `--date-from` | Minimum scope date (YYYY-MM-DD); approval with application/latest-update fallback |
| `--date-to` | Maximum scope date (YYYY-MM-DD); same fallback |
| `--abv-min` | Minimum ABV percentage |
| `--abv-max` | Maximum ABV percentage |
| `--volume-unit` | Package volume unit; required with `--volume-min` or `--volume-max` |
| `--volume-min` | Minimum package volume |
| `--volume-max` | Maximum package volume |
| `--container-type` | Derived container type; can be used multiple times |
| `--limit` | Results per page (max 100) |
| `--page` | Page number |
| `--json` | Output as JSON |

### Permittees

Search and retrieve permittee (alcohol producer/importer) records.

```bash
# Search by company name
cola permittees list -q "diageo"

# Sort text searches by OpenSearch relevance score
cola permittees list -q "diageo" --sort relevance_desc

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

Barcode lookup returns matching approval records from decoded label images. Codes may be missing or repeated across approvals; review the candidate records before treating a match as a product identity. The UPC example uses a code from the [existing whiskey evaluation sample](https://colacloud.us/data-packs/whiskey).

```bash
# Look up by UPC
cola barcode 869357000220

# Look up by EAN
cola barcode 5000281025155

# Output as JSON
cola barcode 869357000220 --json
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

The following tables are illustrative, not verified record fixtures or current plan limits. For real records use the quickstart. Current searches may omit total/page counts.

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

Data commands support `--json` for scripting. These recipes process one page. Without explicit dates the COLA API defaults to the last 365 days. Totals/page counts may be null; continue with `--page` while `pagination.has_more` is true when exporting a bounded query. A text search is not an exact category census:

```bash
# Brand names in this page of bourbon text matches
cola colas list -q "bourbon" --json | jq -r '.data[].brand_name' | sort | uniq

# Count returned-page records by product type
cola colas list --json | jq '.data | group_by(.product_type) | map({type: .[0].product_type, count: length})'

# Export this page of permittees to CSV
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

MIT License covers this CLI; see [LICENSE](LICENSE). Data and label artwork have separate rights and terms.

## Links

- [COLA Cloud Website](https://colacloud.us)
- [API Documentation](https://docs.colacloud.us/api-reference)
- [GitHub Repository](https://github.com/cola-cloud-us/colacloud-cli)

Public support: help@colacloud.us
