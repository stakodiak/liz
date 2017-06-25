
s3_bucket_name = www.cedriceats.com
deploy:
	s3put -b $(s3_bucket_name) --header "Content-Type=text/html" -p "`pwd`/build" build/*
	s3put -b $(s3_bucket_name) -p "`pwd`" assets/css/
deploy-assets:
	s3put -b $(s3_bucket_name) -p "`pwd`" assets/*
clean:
	rm -fr build/
port = 8809
run:
	open -a 'Google Chrome' "http://localhost:$(port)"
	python -m SimpleHTTPServer $(port)
