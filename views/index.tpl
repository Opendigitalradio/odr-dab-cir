<!DOCTYPE html>
<html><head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <title>RTLSDR DAB CIR</title>
	<link rel="stylesheet" href="static/style.css" type="text/css" media="screen" charset="utf-8"/>
</head>
<body>
    <h1>Measure DAB CIR using RTLSDR</h1>

    <ul id="info-nav">
        <li><a href="#general">General</a></li>
    </ul>

    <div id="info">
        <div id="general">
            <p>General Options</p>
            <ul>
                <li>frequency: {{freq}}</li>
                <li>gain: {{gain}}</li>
                <li>rate: {{rate}}</li>
            </ul>
        </div>

        <div id="cir">
            <p>In TM1, maximum component delay is 504 samples at 2048ksps (around 246 us).
                Components that are spaced apart by more than 504 in the graphs below
                are out of the guard interval.
                If you have changed the sampling rate, you must do the conversion yourself.</p>
            <img src="{{fig_file}}" />
        </div>
    </div>
</body>
</html>

