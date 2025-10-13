# FINS REST API

## Analysis Endpoints

### List all analyses
```
GET /api/analyses
```
Returns: Array of analysis packages

### Create new analysis
```
POST /api/analyses
Content-Type: application/json

{
  "name": "Analysis Name",
  "interval": "weekly",           // optional, default: "weekly"
  "time_from": "2009",            // optional, default: "2009"
  "time_to": "2024-12-01",        // optional, default: first of current month
  "hist_bins": 100,               // optional, default: 100
  "hist_min": -80.0,              // optional, default: -80.0
  "hist_max": 80.0,               // optional, default: 80.0
  "mcap_min": "100M",             // optional, default: "100M"
  "inception_max": "2020-01-01"   // optional
}
```
Returns: `{ "package_id": "...", "status": "processing" }`

### Get single analysis
```
GET /api/analysis/{id}
```
Returns: Single analysis package

### Update analysis (rename)
```
PUT /api/analysis/{id}
Content-Type: application/json

{
  "name": "New Analysis Name"
}
```
Returns: Updated analysis package

### Delete analysis
```
DELETE /api/analysis/{id}
```
Returns: 204 No Content

## Response Format

Analysis response is `db.AnalysisPackage`:
```json
{
  "ID": "uuid",
  "Name": "Analysis Name",
  "CreatedAt": "2024-12-15T10:30:00Z",
  "Interval": "weekly",
  "TimeFrom": "2009-01-01T00:00:00Z",
  "TimeTo": "2024-12-01T00:00:00Z",
  "HistBins": 100,
  "HistMin": -80.0,
  "HistMax": 80.0,
  "McapMin": 100000000,
  "InceptionMax": "2020-01-01T00:00:00Z",
  "SymbolCount": 156,
  "Status": "ready" | "processing" | "failed"
}
```

