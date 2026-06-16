# Testing Stages with Tinker

LaraPaper includes a tool called **Tinker** — a command-line interface for running one-off commands against your LaraPaper installation. You'll use it to:

- Force a specific stage to appear on your device for testing
- Push a new render to the device immediately without waiting for the next scheduled refresh
- Revert back to live (real-date) data after testing

You don't need to understand the commands in detail. Just copy and paste them exactly as written.

---

## Opening Tinker

SSH into your server, then run:

```bash
docker exec -it larapaper php artisan tinker
```

You'll see something like:

```
Psy Shell v0.12.x (PHP 8.x) by Justin Hileman
>>>
```

The `>>>` is the Tinker prompt. Type (or paste) commands here and press Enter to run them. Each command runs immediately and shows its result.

To exit Tinker at any time, type `exit` and press Enter, or press Ctrl+D.

**Important:** Paste one line at a time and wait for the `>>>` prompt to return before pasting the next line.

---

## Finding your plugin and device IDs

Before testing, you need to know the ID numbers LaraPaper has assigned to your plugin and device. Run these two commands in Tinker:

```php
App\Models\Plugin::where('name', 'Grand Tour Stage Profile')->first()->id;
```

```php
App\Models\Device::first()->id;
```

Note down the numbers these return. In the examples below, the plugin ID is `36` and the device ID is `1`. Replace these numbers if yours are different.

---

## Testing a specific stage

This is a two-part process: first inject the stage data, then push a new render to the device.

### Step 1 — Get the stage data from the API

On your server (outside Tinker — open a second terminal or exit Tinker first):

```bash
wget -q -O- "http://localhost:5051/api/stage?date=2026-07-09" | python3 -m json.tool
```

Replace `2026-07-09` with the date of any stage you want to test. This shows you what data the recipe would display on that date.

### Step 2 — Inject the data and push to device

Back in Tinker, run these commands one at a time:

```php
$plugin = App\Models\Plugin::find(36);
```

Then paste the data payload as a PHP array. Here's an example for Stage 6 (9 July 2026):

```php
$plugin->data_payload = ["_date_source"=>"query_param","_today"=>"2026-07-09","countdown_days"=>0,"date"=>"2026-07-09","distance_km"=>186,"est_finish"=>"17:05","finish"=>"Gavarnie-Gèdre","image_url"=>"http://YOUR-SERVER-IP:5051/images/2026/tour/stage-06.jpg","short"=>"tour","stage"=>6,"start"=>"Pau","start_time"=>"11:15","status"=>"live","tour"=>"Tour de France","type"=>"mountain","year"=>2026];
```

Then save and render:

```php
$plugin->save();
$plugin->refresh();
$device = App\Models\Device::find(1);
$markup = $plugin->render(device: $device);
App\Jobs\GenerateScreenJob::dispatchSync($device->id, $plugin->id, $markup);
```

Your device will show the new stage on its next refresh (within 5 minutes). You can also manually wake the device by pressing its button.

**Note:** If Tinker shows `Undefined constant ""` after the last command, ignore it — that's a display quirk. The render still completed successfully. You'll see `Generated image:` lines in the output confirming this.

---

## Stage 6 — Quick reference (Pau → Gavarnie-Gèdre)

This is a good test stage as it has prominent mountain climbs and a clear black distance bar.

```php
$plugin = App\Models\Plugin::find(36);
$plugin->data_payload = ["_date_source"=>"query_param","_today"=>"2026-07-09","countdown_days"=>0,"date"=>"2026-07-09","distance_km"=>186,"est_finish"=>"17:05","finish"=>"Gavarnie-Gèdre","image_url"=>"http://YOUR-SERVER-IP:5051/images/2026/tour/stage-06.jpg","short"=>"tour","stage"=>6,"start"=>"Pau","start_time"=>"11:15","status"=>"live","tour"=>"Tour de France","type"=>"mountain","year"=>2026];
$plugin->save();
$plugin->refresh();
$device = App\Models\Device::find(1);
$markup = $plugin->render(device: $device);
App\Jobs\GenerateScreenJob::dispatchSync($device->id, $plugin->id, $markup);
```

---

## Other useful test stages

### Stage 19 — Gap → Alpe d'Huez (mountain, queen stage)

```php
$plugin = App\Models\Plugin::find(36);
$plugin->data_payload = ["_date_source"=>"query_param","_today"=>"2026-07-24","countdown_days"=>0,"date"=>"2026-07-24","distance_km"=>128,"est_finish"=>"15:25","finish"=>"Alpe d'Huez","image_url"=>"http://YOUR-SERVER-IP:5051/images/2026/tour/stage-19.jpg","short"=>"tour","stage"=>19,"start"=>"Gap","start_time"=>"11:15","status"=>"live","tour"=>"Tour de France","type"=>"mountain","year"=>2026];
$plugin->save();
$plugin->refresh();
$device = App\Models\Device::find(1);
$markup = $plugin->render(device: $device);
App\Jobs\GenerateScreenJob::dispatchSync($device->id, $plugin->id, $markup);
```

### Stage 21 — Thoiry → Paris Champs-Élysées (flat, finale)

```php
$plugin = App\Models\Plugin::find(36);
$plugin->data_payload = ["_date_source"=>"query_param","_today"=>"2026-07-26","countdown_days"=>0,"date"=>"2026-07-26","distance_km"=>130,"est_finish"=>"20:15","finish"=>"Paris (Champs-Élysées)","image_url"=>"http://YOUR-SERVER-IP:5051/images/2026/tour/stage-21.jpg","short"=>"tour","stage"=>21,"start"=>"Thoiry","status"=>"live","tour"=>"Tour de France","type"=>"flat","year"=>2026];
$plugin->save();
$plugin->refresh();
$device = App\Models\Device::find(1);
$markup = $plugin->render(device: $device);
App\Jobs\GenerateScreenJob::dispatchSync($device->id, $plugin->id, $markup);
```

---

## Reverting to live data

After testing, always revert the plugin back to real dates so it tracks the actual race:

```php
$plugin = App\Models\Plugin::find(36);
$plugin->polling_url = 'http://YOUR-SERVER-IP:5051/api/stage';
$plugin->save();
$plugin->updateDataPayload();
$plugin->refresh();
$device = App\Models\Device::find(1);
$markup = $plugin->render(device: $device);
App\Jobs\GenerateScreenJob::dispatchSync($device->id, $plugin->id, $markup);
```

Then verify the data source is real:

```php
$plugin->data_payload['_date_source'];
$plugin->data_payload['status'];
$plugin->data_payload['countdown_days'];
```

You should see `"real"`, `"countdown"` (or `"live"` during a race), and the correct number of days.

---

## Forcing a render without changing stage data

If you've updated the markup template and want to push the new version to the device without changing the stage data:

```php
$plugin = App\Models\Plugin::find(36);
$device = App\Models\Device::find(1);
$markup = $plugin->render(device: $device);
App\Jobs\GenerateScreenJob::dispatchSync($device->id, $plugin->id, $markup);
```

This re-renders whatever stage is currently in `data_payload` using the latest markup template.

---

## Checking plugin status

To see the current state of the plugin at any time:

```php
$plugin = App\Models\Plugin::find(36);
$plugin->polling_url;
$plugin->data_payload['status'];
$plugin->data_payload['_date_source'];
$plugin->data_payload['stage'];
```

This tells you: what URL is being polled, whether data is from a real date or a test override, and which stage is currently loaded.
