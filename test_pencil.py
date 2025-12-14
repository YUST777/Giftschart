#!/usr/bin/env python3
import asyncio
import traceback
from new_card_design import create_gift_card

async def test():
    try:
        result = await create_gift_card('Pencil', output_path='new_gift_cards/Pencil.png', force_fresh=True)
        print('Success:', result is not None)
        if result:
            print('Card generated successfully!')
        else:
            print('Card generation returned None')
    except Exception as e:
        print('Error:', e)
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())

