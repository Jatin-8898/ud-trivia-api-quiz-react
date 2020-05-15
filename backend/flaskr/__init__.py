import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
	page = request.args.get('page', 1, type=int)
	start = (page - 1) * QUESTIONS_PER_PAGE
	end = start + QUESTIONS_PER_PAGE

	questions = [question.format() for question in selection]
	current_questions = questions[start:end]

	return current_questions
	
def create_app(test_config=None):
	# create and configure the app
	app = Flask(__name__)
	setup_db(app)
	
	'''
	@TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
	'''
	CORS(app)
	'''
	@TODO: Use the after_request decorator to set Access-Control-Allow
	'''
	@app.after_request
	def after_request(response):
		response.headers.add('Access-Control-Allow-Headers','Content-Type,Authorization,true')
		response.headers.add('Access-Control-Allow-Methods','GET,PUT,POST,DELETE,OPTIONS')
		return response
	'''
	@TODO: 
	Create an endpoint to handle GET requests 
	for all available categories.
	'''
	@app.route('/categories')
	def get_categories():
		categories = Category.query.order_by(Category.type).all()

		if len(categories) == 0:
			abort(404)

		return jsonify({
			'success': True,
			'categories': {category.id: category.type for category in categories}
		})

	'''
	@TODO: 
	Create an endpoint to handle GET requests for questions, 
	including pagination (every 10 questions). 
	This endpoint should return a list of questions, 
	number of total questions, current category, categories. 

	TEST: At this point, when you start the application
	you should see questions and categories generated,
	ten questions per page and pagination at the bottom of the screen for three pages.
	Clicking on the page numbers should update the questions. 
	'''
	@app.route('/questions')
	def get_questions():
		selection = Question.query.order_by(Question.id).all()
		current_questions = paginate_questions(request, selection)

		categories = Category.query.order_by(Category.type).all()

		if len(current_questions) == 0:
			abort(404)

		return jsonify({
			'success': True,
			'questions': current_questions,
			'total_questions': len(selection),
			'categories': {category.id: category.type for category in categories},
			'current_category': None
		})
	'''
	@TODO: 
	Create an endpoint to DELETE question using a question ID. 

	TEST: When you click the trash icon next to a question, the question will be removed.
	This removal will persist in the database and when you refresh the page. 
	'''
	@app.route("/questions/<question_id>", methods=['DELETE'])
	def delete_question(question_id):
		question = Question.query.filter(Question.id == question_id).one_or_none()
		if not question:
			# If no question with given id was found, raise 404 
			abort(400, {'message': 'Question with id {} does not exist.'.format(question_id)})
		try:
			question.delete()
			return jsonify({
				'success': True,
				'deleted': question_id
			})
		except:
			abort(422)
	'''
	@TODO: 
	Create an endpoint to POST a new question, 
	which will require the question and answer text, 
	category, and difficulty score.

	TEST: When you submit a question on the "Add" tab, 
	the form will clear and the question will appear at the end of the last page
	of the questions list in the "List" tab.  
	'''
	@app.route("/questions", methods=['POST'])
	def add_question():
		body = request.get_json()

		question = body.get('question')
		answer = body.get('answer')
		category = body.get('category')
		difficulty = body.get('difficulty')

		# Check all the fiels are present
		if not question:
			abort(400, {'message': 'Question can not be blank'})

		if not answer:
			abort(400, {'message': 'Answer can not be blank'})

		if not category:
			abort(400, {'message': 'Category can not be blank'})

		if not difficulty:
			abort(400, {'message': 'Difficulty can not be blank'})

		try:
			question = Question(
				question=question, 
				answer=answer, 
				difficulty=difficulty, 
				category=category)
			question.insert()

			# After succesfully insertion, get all the  paginated questionss 
			selections = Question.query.order_by(Question.id).all()
			questions_paginated = paginate_questions(request, selections)

			return jsonify({
				'success': True,
				'created': question.id,
				'questions': questions_paginated,
        		'total_questions': len(selections)
			})
		except:
			abort(422)
	'''
	@TODO: 
	Create a POST endpoint to get questions based on a search term. 
	It should return any questions for whom the search term 
	is a substring of the question. 

	TEST: Search by any phrase. The questions list will update to include 
	only question that include that string within their question. 
	Try using the word "title" to start. 
	'''
	@app.route('/questions/search', methods=['POST'])
	def search_questions():
		body = request.get_json()
		search_term = body.get('searchTerm', None)
		try:
			if search_term:
				search_results = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

				return jsonify({
					'success': True,
					'questions': [question.format() for question in search_results],
					'total_questions': len(search_results),
					'current_category': None
				})
		except:	
			abort(404)
	'''
	@TODO: 
	Create a GET endpoint to get questions based on category. 

	TEST: In the "List" tab / main screen, clicking on one of the 
	categories in the left column will cause only questions of that 
	category to be shown. 
	'''
	@app.route('/categories/<int:category_id>/questions', methods=['GET'])
	def get_questions_by_category(category_id):
		try:
			questions = Question.query.filter(Question.category == str(category_id)).all()

			return jsonify({
				'success': True,
				'questions': [question.format() for question in questions],
				'total_questions': len(questions),
				'current_category': category_id
			})
		except:
			abort(404)

	'''
	@TODO: 
	Create a POST endpoint to get questions to play the quiz. 
	This endpoint should take category and previous question parameters 
	and return a random questions within the given category, 
	if provided, and that is not one of the previous questions. 

	TEST: In the "Play" tab, after a user selects "All" or a category,
	one question at a time is displayed, the user is allowed to answer
	and shown whether they were correct or not. 
	'''
	@app.route('/quizzes', methods=['POST'])
	def play_quiz():
		body = request.get_json()
		if not body:
			# If no json body given, raise error.
			abort(400, {'message': 'Please provide a JSON body with previous Question Ids and optional category. Thanks'})
		try:
			# Get paramters from JSON Body.
			previous_questions = body.get('previous_questions', None)
			category = body.get('quiz_category', None)

			if category['type'] == 'click':
				available_questions = (Question.query
								.filter(Question.id.notin_((previous_questions)))
								.all())
			else:
				available_questions = (Question.query
								.filter_by(category=category['id'])
								.filter(Question.id.notin_((previous_questions)))
								.all())

			 # Format questions & get a random question
			questions_formatted = [question.format() for question in available_questions]
			random_question = questions_formatted[random.randint(0, len(questions_formatted))]
	
			return jsonify({
				'success': True,
				'question': random_question
			})
		except:
			abort(422)
	'''
	BONUS: API to create and delete Categories
	'''
	@app.route('/categories', methods=['POST'])
	def create_categories():
		body = request.get_json()

		if not body:
			abort(400, {'message': 'Request does not contain a valid JSON body.'})

		# Get field informations from request body
		type = body.get('type', None)

		# Check all required fields are given.
		if not type:
			abort(400, {'message': 'No type for New category provided.'})
		try:
			category = Category(type = type)
			category.insert()

			# After succesfully insertion, get all categories 
			selections = Category.query.order_by(Category.id).all()
			categories_all = [category.format() for category in selections]

			# Return response
			return jsonify({
				'success': True,
				'created': category.id,
				'categories': categories_all,
				'total_categories': len(selections)
			})
		except:
			abort(422)

	@app.route('/categories/<int:category_id>', methods=['DELETE'])
	def delete_categories(category_id):
		category = Category.query.filter(Category.id == category_id).one_or_none()
		
		if not category:
			# If no category with given id was found, raise 404 and explain what went wrong.
			abort(400, {'message': 'Category with id {} does not exist.'.format(category_id)})
		try:
			category.delete()
			return jsonify({
				'success': True,
				'deleted': category_id
			})
		except:
			abort(422)
	'''
	@TODO: 
	Create error handlers for all expected errors 
	including 404 and 422. 
	'''
	@app.errorhandler(400)
	def bad_request(error):
		return jsonify({
			"success": False, 
			"error": 400,
			"message": "bad request"
		}), 400

	@app.errorhandler(404)
	def ressource_not_found(error):
		return jsonify({
			"success": False, 
			"error": 404,
			"message": "resource not found"
		}), 404

	@app.errorhandler(405)
	def method_not_allowed(error):
		return jsonify({
			"success": False, 
			"error": 405,
			"message": "method not allowed"
		}), 405

	@app.errorhandler(422)
	def unprocessable(error):
		return jsonify({
			"success": False, 
			"error": 422,
			"message": "unprocessable"
		}), 422
	
	@app.errorhandler(500)
	def internal_server_error(error):
		return jsonify({
			"success": False, 
			"error": 500,
			"message": "internal server error"
		}), 500

	return app