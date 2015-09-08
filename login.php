<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<title>Login :: What.CD</title>
	<meta http-equiv="X-UA-Compatible" content="chrome=1; IE=edge" />
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<link rel="shortcut icon" href="favicon.ico" />
	<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
	<link href="static/styles/public/style.css?v=1381233767" rel="stylesheet" type="text/css" />
	<script src="static/functions/jquery.js" type="text/javascript"></script>
	<script src="static/functions/script_start.js?v=1424742299" type="text/javascript"></script>
	<script src="static/functions/ajax.class.js?v=1401309905" type="text/javascript"></script>
	<script src="static/functions/cookie.class.js?v=1369678528" type="text/javascript"></script>
	<script src="static/functions/storage.class.js?v=1369678528" type="text/javascript"></script>
	<script src="static/functions/global.js?v=1389996001" type="text/javascript"></script>
</head>
<body>
<div id="head">
</div>
<table class="layout" id="maincontent">
	<tr>
		<td align="center" valign="middle">
			<div id="logo">
				<ul>
					<li><a href="index.php">Home</a></li>
					<li><a href="login.php">Log in</a></li>
				</ul>
			</div>
	<span id="no-cookies" class="hidden warning">You appear to have cookies disabled.<br /><br /></span>
	<noscript><span class="warning">What.CD requires JavaScript to function properly. Please enable JavaScript in your browser.</span><br /><br /></noscript>
	<form class="auth_form" name="login" id="loginform" method="post" action="login.php">
	<span class="warning">Your username or password was incorrect.<br /><br /></span>
	You have <span class="info">5</span> attempts remaining.<br /><br />
	<strong>WARNING:</strong> You will be banned for 6 hours after your login attempts run out!<br /><br />
	<table class="layout">
		<tr>
			<td>Username&nbsp;</td>
			<td colspan="2">
				<input type="text" name="username" id="username" class="inputtext" required="required" maxlength="20" pattern="[A-Za-z0-9_?\.]{1,20}" autofocus="autofocus" placeholder="Username" />
			</td>
		</tr>
		<tr>
			<td>Password&nbsp;</td>
			<td colspan="2">
				<input type="password" name="password" id="password" class="inputtext" required="required" maxlength="100" pattern=".{6,100}" placeholder="Password" />
			</td>
		</tr>
		<tr>
			<td></td>
			<td>
				<input type="checkbox" id="keeplogged" name="keeplogged" value="1" />
				<label for="keeplogged">Remember me</label>
			</td>
			<td><input type="submit" name="login" value="Log in" class="submit" /></td>
		</tr>
	</table>
	</form>
	<br /><br />
	Lost your password? <a href="login.php?act=recover" class="tooltip" title="Recover your password">Recover it here!</a>
<script type="text/javascript" src="static/functions/detect_mobile.js"></script>
<script type="text/javascript">
cookie.set('cookie_test', 1, 1);
if (cookie.get('cookie_test') != null) {
	cookie.del('cookie_test');
} else {
	$('#no-cookies').gshow();
}
</script>
		</td>
	</tr>
</table>
<div id="foot">
	<span><a href="#">What.CD</a> | <a href="https://what.cd/gazelle/">Project Gazelle</a></span>
</div>
</body>
</html>
