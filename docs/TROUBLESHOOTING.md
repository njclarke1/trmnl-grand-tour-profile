# Troubleshooting

Common problems and how to fix them.

---

## The device isn't updating

**Check the container is running:**

```bash
wget -q -O- http://localhost:5051/health
```

Should return `{"status":"ok"}`. If it doesn't, restart the container:

```bash
docker restart grand-tour
```

**Check when the device last polled:**

In Tinker:

```php
App\Models\Device::first()->last_refreshed_at;
```

The device polls every 5 minutes (`default_refresh_interval: 300`). If `last_refreshed_at` is recent, it's polling correctly.

**Check the device logs:**

```php
App\Models\Device::first()->last_log_request;
```

Look for error messages — common ones are WiFi connectivity issues or timeout errors reaching the server.

---

## Preview shows "No stage data available"

The template rendered but the API returned no usable data. Check:

**1. Is the API reachable from LaraPaper?**

```bash
docker exec larapaper wget -q -O- http://YOUR-SERVER-IP:5051/api/stage
```

If this fails, LaraPaper can't reach the grand-tour container. Check both containers are on the same Docker network or that port 5051 is accessible.

**2. Are the schedule files mounted?**

```bash
docker exec grand-tour ls /data/
```

You should see year folders (e.g. `2026`). If empty, the volume mount in your Portainer stack is pointing to the wrong path.

**3. Does the JSON have valid dates?**

```bash
wget -q -O- http://localhost:5051/api/stage | python3 -m json.tool
```

If `status` is `"no_data"`, the schedule files exist but contain no stages. Check the JSON files for formatting errors.

---

## Images aren't displaying (broken image on device)

**Check the image URL from the API:**

```bash
wget -q -O- http://localhost:5051/api/stage | python3 -m json.tool
```

Note the `image_url` field, then test it directly:

```bash
wget -q -O /dev/null "THE_IMAGE_URL" && echo "OK" || echo "FAIL"
```

**Common causes:**

- Image file doesn't exist at the expected path — check the `image` field in your JSON matches the actual filename
- `short` field in JSON doesn't match the folder name (`tour`, `giro`, or `vuelta`)
- `BASE_URL` in Portainer stack doesn't match your server's actual IP

---

## Variables not resolving in the template (showing `{{ $status }}` literally)

LaraPaper uses `$data['key']` to access polling JSON. The template is already written for this. If variables aren't resolving, check:

1. The plugin's **Data strategy** is set to `polling` (not `push` or `static`)
2. The **Polling URL** is correct and reachable
3. The plugin has successfully polled at least once — check the Data tab in the plugin editor for a JSON preview

---

## "Undefined variable $payload" error

The template uses `$data`, not `$payload`. This error means an old version of the markup is loaded. Replace the markup with the current contents of `recipe/markup.blade.php`.

---

## Device showing wrong resolution (content appears in top-left corner only)

The device model isn't set correctly in LaraPaper. For M5Stack PaperS3:

In Tinker:

```php
$device = App\Models\Device::first();
$device->width = 960;
$device->height = 540;
$device->save();
```

Also verify `device_model_id` is `28`:

```php
App\Models\Device::first()->device_model_id;
```

If it returns something other than `28`, set it:

```php
$device = App\Models\Device::first();
$device->device_model_id = 28;
$device->save();
```

---

## "Connection refused" errors in device logs

The device can't reach LaraPaper. This is usually a network issue, not a recipe issue. Check:

- LaraPaper is running (`docker ps | grep larapaper`)
- The device is on the same WiFi network as the server
- The server's IP hasn't changed (consider setting a static local IP on the server)

---

## Cache not clearing after updating images

If you replace a stage image file but the old processed version keeps serving:

```bash
rm -f /YOUR/PATH/grand-tour/cache/*.png
docker restart grand-tour
```

The cache is rebuilt automatically on the next request. The cache key includes the source file's modification time, so replacing a file with a new one of the same name will also automatically bust the cache on next request.

---

## Getting help

If you're stuck, the most useful thing to include when asking for help is the output of:

```bash
wget -q -O- http://localhost:5051/api/stage | python3 -m json.tool
docker logs grand-tour 2>&1 | tail -20
```

These show the current API state and any recent errors from the container.
