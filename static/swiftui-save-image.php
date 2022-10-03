<?php
	
	// get image
	$image = $_POST["image"];

	// replace spaces with +
	$data = str_replace(" ", "+", $image);

	// decoding base 64
	foreach ($_POST["images"] as $image)
	{
    		$data = base64_decode($data);
	}

	// saving in files as image
	file_put_contents("image.jpeg", $data);

	// sending response back
	echo "Done";
?>
