<!--
  TRMNL Grand Tour Stage Profile — Recipe Markup (Blade)
  Optimised for 960×540 (M5Stack PaperS3)

  LaraPaper exposes the polling JSON response as $data (associative array,
  14 keys matching the /api/stage response). Confirmed via dd(get_defined_vars()).
-->

<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700&display=swap" rel="stylesheet">

<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --font-condensed: 'Barlow Condensed', 'Arial Narrow', Arial, sans-serif;
  }

  .screen {
    width: 960px;
    height: 540px;
    margin: 0 auto;
    background: #fff;
    color: #000;
    font-family: var(--font-condensed);
    overflow: hidden;
    position: relative;
  }

  /* --- STAGE LAYOUT --- */
  .stage-view {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 0;
  }

  .strip {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    height: 40px;
    min-height: 40px;
    flex-shrink: 0;
  }

  .tour-abbr {
    font-size: 26px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    min-width: 80px;
  }

  .stage-number {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .badge {
    display: inline-block;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    border: 2px solid #000;
    padding: 1px 8px;
    margin-left: 10px;
    vertical-align: middle;
  }

  .stage-date {
    font-size: 22px;
    font-weight: 400;
    color: #333;
    text-align: right;
    letter-spacing: 0.5px;
  }

  .profile-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    min-height: 0;
  }

  .profile-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  /* --- COUNTDOWN LAYOUT --- */
  .countdown-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    text-align: center;
  }

  .countdown-tour {
    width: 100%;
    text-align: center;
    font-size: 48px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 6px;
    margin-bottom: 24px;
  }

  .countdown-number {
    width: 100%;
    text-align: center;
    font-size: 160px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
    letter-spacing: -2px;
  }

  .countdown-label {
    width: 100%;
    text-align: center;
    font-size: 36px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 8px;
    margin-bottom: 32px;
  }

  .countdown-start {
    width: 100%;
    text-align: center;
    font-size: 26px;
    font-weight: 400;
    color: #444;
    letter-spacing: 1px;
  }

  /* --- ERROR / NO DATA --- */
  .error-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    padding: 40px;
  }

  .error-message {
    font-size: 24px;
    color: #666;
  }
</style>

@php
  $status = $data['status'] ?? null;
  $tour = $data['tour'] ?? null;
  $short = $data['short'] ?? null;
  $stage = $data['stage'] ?? null;
  $date = $data['date'] ?? '';
  $start = $data['start'] ?? '';
  $finish = $data['finish'] ?? '';
  $type = $data['type'] ?? '';
  $distance_km = $data['distance_km'] ?? '';
  $image_url = $data['image_url'] ?? null;
  $countdown_days = $data['countdown_days'] ?? null;

  $tour_abbr = match($short) {
    'tour'   => 'TdF',
    'giro'   => 'Giro',
    'vuelta' => 'Vuelta',
    default  => $tour,
  };

  $date_formatted = '';
  if ($date) {
    try {
      $date_formatted = \Carbon\Carbon::parse($date)->format('l j F Y');
    } catch (\Exception $e) {
      $date_formatted = $date;
    }
  }
@endphp

{{-- Countdown / off-season mode --}}
@if ($status === 'countdown' || $status === 'off_season')
<div class="screen">
  <div class="countdown-view">
    <div class="countdown-tour">{{ $tour_abbr }}</div>
    @if (!empty($countdown_days))
      <div class="countdown-number">{{ $countdown_days }}</div>
      <div class="countdown-label">days to go</div>
    @endif
    <div class="countdown-start">{{ $date_formatted ?: $date }}</div>
  </div>
</div>

{{-- Stage display (live / rest_day / upcoming) --}}
@elseif (!empty($image_url))
<div class="screen">
  <div class="stage-view">
    <div class="strip">
      <span class="tour-abbr">{{ $tour_abbr }}</span>
      <span class="stage-number">
        Stage {{ $stage }}
        @if ($status === 'rest_day')
          <span class="badge">Next up</span>
        @elseif ($status === 'upcoming')
          <span class="badge">{{ $countdown_days }} days</span>
        @endif
      </span>
      <span class="stage-date">{{ $date_formatted }}</span>
    </div>
    <div class="profile-container">
      <img src="{{ $image_url }}" class="profile-image" alt="Stage {{ $stage }} profile" />
    </div>
  </div>
</div>

{{-- Fallback --}}
@else
<div class="screen">
  <div class="error-view">
    <div class="error-message">No stage data available.<br>Check schedule files.</div>
  </div>
</div>
@endif
