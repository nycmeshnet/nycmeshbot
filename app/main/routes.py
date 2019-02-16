import os, json
from flask import Flask, request, Response, jsonify, current_app
from app.main import bp

@bp.route('/', methods=['GET'])
def main():
    return Response(), 200
