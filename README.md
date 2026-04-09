# Solar Windows

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant integration that tracks which windows in your home have direct sunlight shining through them right now, based on the sun's current position and local weather conditions.

Each window becomes a `binary_sensor` entity — **on** when the sun is shining through it, **off** when it isn't. Use these sensors in any automation, dashboard, or condition you like.

---

## What it does

- Creates a `binary_sensor` for every window you configure
- Uses Home Assistant's built-in `sun.sun` entity for real-time sun azimuth and elevation
- Optionally checks your weather entity to suppress sun shining status on overcast days
- Updates every 2 minutes automatically
- Exposes useful attributes: sun azimuth, elevation, azimuth difference, weather state

---

## Installation via HACS

1. Open HACS in your Home Assistant sidebar
2. Go to **Integrations**
3. Click the three-dot menu → **Custom repositories**
4. Add `https://github.com/Pine0981/ha-solar-windows` as an **Integration**
5. Search for "Solar Windows" and click **Download**
6. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Solar Windows**
3. Configure global settings:
   - **Weather entity** — used to detect overcast conditions (default: `weather.home`)
   - **Sun cone** — degrees either side of a window's facing direction that count as "sun shining in" (default: 65°)
   - **Minimum elevation** — sun must be this many degrees above the horizon (default: 5°)
4. Add your windows one by one — give each a name and select which compass direction it faces

---

## Example entities

After setup you'll have entities like:

```
binary_sensor.living_room_south_window_sun_shining
binary_sensor.bedroom_east_window_sun_shining
binary_sensor.kitchen_window_sun_shining
```

When the entity is **on**, sun is shining through that window. When **off**, it isn't.

Each entity has these attributes:

| Attribute | Description |
|---|---|
| `facing` | Compass direction the window faces (N/NE/E etc.) |
| `facing_azimuth` | Numeric azimuth of the facing direction |
| `sun_azimuth` | Current sun azimuth from `sun.sun` |
| `sun_elevation` | Current sun elevation from `sun.sun` |
| `azimuth_diff` | Degrees between sun and window facing |
| `weather_state` | Current state of your weather entity |
| `sun_cone_degrees` | Configured cone width |

---

## Example automations

### Turn off lights when sun shines in

```yaml
automation:
  - alias: "Turn off living room light when sun shines in"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_south_window_sun_shining
        to: "on"
    action:
      - service: light.turn_off
        target:
          entity_id: light.living_room
```

### Turn lights back on when sun is gone

```yaml
automation:
  - alias: "Turn on living room light when sun is no longer shining in"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_south_window_sun_shining
        to: "off"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
```

### Use as a condition in any automation

```yaml
condition:
  - condition: state
    entity_id: binary_sensor.living_room_south_window_sun_shining
    state: "off"
```

---

## How sun detection works

A window is considered **sun shining in** when all three conditions are true:

1. The sun's azimuth is within `sun_cone` degrees of the window's facing direction
2. The sun's elevation is above `min_elevation` degrees
3. The weather entity is not in an overcast state (cloudy, rainy, snowy, etc.)

The default cone of 65° means a south-facing window (180°) will have sun shining in when the sun is anywhere between 115° and 245°.

---

## Editing windows after setup

Go to **Settings → Devices & Services → Solar Windows → Configure** to adjust settings or edit your windows list.

---

## Requirements

- Home Assistant 2023.1.0 or newer
- The built-in `sun` integration must be enabled (it is by default)
- A `weather` entity is recommended but optional
